import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.api.deps import SessionDep
from app.core.config import settings
from app.modules.brands.deps import BrandMembership, BrandOwner
from app.modules.content.api import get_draft_or_404
from app.modules.generations.models import GeneratedAsset, IntegrityStatus
from app.modules.publishing.models import (
    ConnectionStatus,
    PublishJob,
    PublishStatus,
    SocialConnection,
)
from app.modules.publishing.schemas import (
    PublishJobPublic,
    PublishJobsPublic,
    SocialConnectionPublic,
    SocialConnectionUpdate,
)
from app.modules.publishing.service import PublishError, can_publish
from app.workers.tasks import enqueue_publish

router = APIRouter(prefix="/brands/{brand_id}", tags=["Publishing"])

MAX_PUBLISH_ATTEMPTS = 3


def _connection_public(connection: SocialConnection) -> SocialConnectionPublic:
    return SocialConnectionPublic(
        provider=connection.provider,
        external_account_id=connection.external_account_id,
        account_name=connection.account_name,
        status=connection.status,
        token_expires_at=connection.token_expires_at,
        updated_at=connection.updated_at,
    )


def _job_public(job: PublishJob) -> PublishJobPublic:
    return PublishJobPublic(
        id=job.id,
        draft_id=job.draft_id,
        provider=job.provider,
        status=job.status,
        remote_post_id=job.remote_post_id,
        remote_post_url=job.remote_post_url,
        error_message=job.error_message,
        attempt_count=job.attempt_count,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _get_connection(session: SessionDep, brand_id: uuid.UUID) -> SocialConnection | None:
    return session.exec(
        select(SocialConnection).where(SocialConnection.brand_id == brand_id)
    ).first()


@router.get("/social", response_model=SocialConnectionPublic | None)
def read_connection(
    session: SessionDep, membership: BrandMembership
) -> SocialConnectionPublic | None:
    connection = _get_connection(session, membership.brand_id)
    return _connection_public(connection) if connection else None


@router.put("/social", response_model=SocialConnectionPublic)
def connect_social(
    *,
    session: SessionDep,
    owner: BrandOwner,
    connection_in: SocialConnectionUpdate,
) -> SocialConnectionPublic:
    connection = _get_connection(session, owner.brand_id)
    if not connection:
        connection = SocialConnection(brand_id=owner.brand_id)
    if (
        settings.INSTAGRAM_PROVIDER == "graph"
        and not connection_in.access_token
        and not connection.access_token
    ):
        raise HTTPException(
            status_code=400,
            detail="An Instagram access token is required for the Graph provider",
        )
    connection.external_account_id = connection_in.external_account_id
    connection.account_name = connection_in.account_name
    if connection_in.access_token:
        connection.access_token = connection_in.access_token
    elif settings.INSTAGRAM_PROVIDER == "fake" and not connection.access_token:
        connection.access_token = "fake-token"
    connection.token_expires_at = connection_in.token_expires_at
    connection.status = ConnectionStatus.CONNECTED.value
    connection.updated_at = datetime.now(UTC)
    session.add(connection)
    session.commit()
    session.refresh(connection)
    return _connection_public(connection)


@router.delete("/social", response_model=SocialConnectionPublic)
def disconnect_social(
    session: SessionDep, owner: BrandOwner
) -> SocialConnectionPublic:
    connection = _get_connection(session, owner.brand_id)
    if not connection:
        raise HTTPException(status_code=404, detail="No social connection")
    connection.status = ConnectionStatus.DISCONNECTED.value
    connection.access_token = None
    connection.updated_at = datetime.now(UTC)
    session.add(connection)
    session.commit()
    session.refresh(connection)
    return _connection_public(connection)


@router.post("/drafts/{draft_id}/publish", response_model=PublishJobPublic)
async def publish_draft(
    session: SessionDep, owner: BrandOwner, draft_id: uuid.UUID
) -> PublishJobPublic:
    draft = get_draft_or_404(session, owner.brand_id, draft_id)
    # Idempotency: repeated clicks return the in-flight or completed job.
    existing = session.exec(
        select(PublishJob).where(PublishJob.draft_id == draft.id)
    ).all()
    for job in existing:
        if job.status in {
            PublishStatus.QUEUED.value,
            PublishStatus.PROCESSING.value,
            PublishStatus.PUBLISHED.value,
        }:
            return _job_public(job)
    try:
        can_publish(session, draft, owner.brand_id)
    except PublishError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job = PublishJob(
        brand_id=owner.brand_id,
        draft_id=draft.id,
        provider=settings.INSTAGRAM_PROVIDER,
        status=PublishStatus.QUEUED.value,
    )
    session.add(job)
    try:
        session.commit()
    except IntegrityError:
        # A concurrent request won the idempotency race.
        session.rollback()
        existing_jobs = session.exec(
            select(PublishJob).where(
                PublishJob.draft_id == draft.id,
                PublishJob.status != PublishStatus.FAILED.value,
            )
        ).all()
        if existing_jobs:
            return _job_public(existing_jobs[0])
        raise HTTPException(status_code=409, detail="Publish already in progress")
    session.refresh(job)
    try:
        await enqueue_publish(job.id)
    except PublishError:
        pass
    session.expire_all()
    refreshed = session.get(PublishJob, job.id)
    if not refreshed:
        raise HTTPException(status_code=500, detail="Publish job lost")
    return _job_public(refreshed)


@router.get("/drafts/{draft_id}/publish-jobs", response_model=PublishJobsPublic)
def read_publish_jobs(
    session: SessionDep, membership: BrandMembership, draft_id: uuid.UUID
) -> PublishJobsPublic:
    draft = get_draft_or_404(session, membership.brand_id, draft_id)
    jobs = session.exec(
        select(PublishJob).where(PublishJob.draft_id == draft.id)
    ).all()
    jobs = sorted(jobs, key=lambda job: job.created_at, reverse=True)
    data = [_job_public(job) for job in jobs]
    return PublishJobsPublic(data=data, count=len(data))


@router.post("/publish-jobs/{job_id}/retry", response_model=PublishJobPublic)
async def retry_publish(
    session: SessionDep, owner: BrandOwner, job_id: uuid.UUID
) -> PublishJobPublic:
    job = session.get(PublishJob, job_id)
    if not job or job.brand_id != owner.brand_id:
        raise HTTPException(status_code=404, detail="Publish job not found")
    if job.status != PublishStatus.FAILED.value:
        raise HTTPException(status_code=400, detail="Only failed jobs can retry")
    if job.attempt_count >= MAX_PUBLISH_ATTEMPTS:
        raise HTTPException(status_code=400, detail="Retry limit reached")
    draft = get_draft_or_404(session, owner.brand_id, job.draft_id)
    asset = session.get(GeneratedAsset, draft.generated_asset_id)
    if not asset or asset.integrity_status == IntegrityStatus.FAILED.value:
        raise HTTPException(status_code=400, detail="Asset no longer publishable")
    job.status = PublishStatus.QUEUED.value
    job.error_message = None
    job.updated_at = datetime.now(UTC)
    draft.status = "approved"
    session.add(job)
    session.add(draft)
    session.commit()
    try:
        await enqueue_publish(job.id)
    except PublishError:
        pass
    session.expire_all()
    refreshed = session.get(PublishJob, job.id)
    if not refreshed:
        raise HTTPException(status_code=500, detail="Publish job lost")
    return _job_public(refreshed)

