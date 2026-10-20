import uuid
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.modules.content.models import ContentDraft, DraftStatus
from app.modules.generations.models import GeneratedAsset, IntegrityStatus
from app.modules.publishing.models import (
    ConnectionStatus,
    PublishJob,
    PublishStatus,
    SocialConnection,
)
from app.providers.instagram import InstagramError, publish_image
from app.providers.storage import get_storage


class PublishError(Exception):
    pass


def _compose_caption(draft: ContentDraft) -> str:
    parts = [draft.caption.strip()]
    if draft.cta:
        parts.append(draft.cta.strip())
    if draft.hashtags:
        parts.append(draft.hashtags.strip())
    return "\n\n".join(part for part in parts if part)


def run_publish(session: Session, job_id: uuid.UUID) -> PublishJob:
    job = session.get(PublishJob, job_id)
    if not job:
        raise PublishError("Publish job not found")
    draft = session.get(ContentDraft, job.draft_id)
    if not draft:
        raise PublishError("Content draft not found")
    connection = session.exec(
        select(SocialConnection).where(SocialConnection.brand_id == job.brand_id)
    ).first()
    asset = session.get(GeneratedAsset, draft.generated_asset_id)
    if not connection or connection.status != ConnectionStatus.CONNECTED.value:
        raise PublishError("Instagram is not connected")
    if not asset:
        raise PublishError("Generated asset is missing")

    job.status = PublishStatus.PROCESSING.value
    job.attempt_count += 1
    job.updated_at = datetime.now(UTC)
    session.add(job)
    session.commit()

    try:
        image_bytes = get_storage().read(asset.storage_key)
        image_url = get_storage().presigned_url(asset.storage_key, 900)
        result = publish_image(
            image_bytes, _compose_caption(draft), connection, image_url
        )
    except Exception as exc:  # noqa: BLE001
        job.status = PublishStatus.FAILED.value
        job.error_message = (
            str(exc)[:900] if isinstance(exc, InstagramError) else "Publishing failed"
        )
        job.updated_at = datetime.now(UTC)
        draft.status = DraftStatus.PUBLISH_FAILED.value
        draft.updated_at = datetime.now(UTC)
        session.add(job)
        session.add(draft)
        session.commit()
        raise PublishError(job.error_message) from exc

    job.status = PublishStatus.PUBLISHED.value
    job.remote_post_id = result.remote_post_id
    job.remote_post_url = result.remote_post_url
    job.updated_at = datetime.now(UTC)
    draft.status = DraftStatus.PUBLISHED.value
    draft.updated_at = datetime.now(UTC)
    session.add(job)
    session.add(draft)
    session.commit()
    session.refresh(job)
    return job


def can_publish(session: Session, draft: ContentDraft, brand_id: uuid.UUID) -> None:
    if draft.status != DraftStatus.APPROVED.value:
        raise PublishError("Only approved content can be published")
    asset = session.get(GeneratedAsset, draft.generated_asset_id)
    if not asset:
        raise PublishError("Generated asset is missing")
    if asset.integrity_status in {
        IntegrityStatus.FAILED.value,
        IntegrityStatus.PENDING.value,
    }:
        raise PublishError("This asset did not pass the integrity gate")
    connection = session.exec(
        select(SocialConnection).where(SocialConnection.brand_id == brand_id)
    ).first()
    if not connection or connection.status != ConnectionStatus.CONNECTED.value:
        raise PublishError("Connect an Instagram account first")
