import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.modules.brands.deps import BrandMembership
from app.modules.content.models import ContentDraft, DraftStatus
from app.modules.content.schemas import (
    CaptionGenerateRequest,
    ContentDraftCreate,
    ContentDraftDetail,
    ContentDraftPublic,
    ContentDraftsPublic,
    ContentDraftUpdate,
)
from app.modules.content.service import (
    CaptionGenerationError,
    asset_belongs_to_brand,
    draft_detail_fields,
    generate_caption_for_draft,
)

router = APIRouter(prefix="/brands/{brand_id}/drafts", tags=["Content"])


def _public(draft: ContentDraft) -> ContentDraftPublic:
    return ContentDraftPublic(
        id=draft.id,
        brand_id=draft.brand_id,
        product_id=draft.product_id,
        generated_asset_id=draft.generated_asset_id,
        caption=draft.caption,
        alternative_captions_json=draft.alternative_captions_json,
        hashtags=draft.hashtags,
        cta=draft.cta,
        status=draft.status,
        created_by=draft.created_by,
        approved_by=draft.approved_by,
        approved_at=draft.approved_at,
        user_edited=draft.user_edited,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


def _detail(session: SessionDep, draft: ContentDraft) -> ContentDraftDetail:
    asset, request, product, profile, model = draft_detail_fields(session, draft)
    return ContentDraftDetail(
        **_public(draft).model_dump(),
        generation_request_id=request.id,
        integrity_status=asset.integrity_status,
        integrity_findings_json=asset.integrity_findings_json,
        product_name=product.name,
        product_category=product.category,
        brand_profile_version=profile.version,
        model_name=model.name if model else None,
    )


def get_draft_or_404(
    session: SessionDep, brand_id: uuid.UUID, draft_id: uuid.UUID
) -> ContentDraft:
    draft = session.get(ContentDraft, draft_id)
    if not draft or draft.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Content draft not found")
    return draft


@router.post("", response_model=ContentDraftDetail)
def create_draft(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    membership: BrandMembership,
    draft_in: ContentDraftCreate,
) -> ContentDraftDetail:
    try:
        asset, request = asset_belongs_to_brand(
            session, draft_in.generated_asset_id, membership.brand_id
        )
    except CaptionGenerationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    draft = ContentDraft(
        brand_id=membership.brand_id,
        product_id=request.product_id,
        generated_asset_id=asset.id,
        created_by=current_user.id,
        status=DraftStatus.DRAFT.value,
    )
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return _detail(session, draft)


@router.get("", response_model=ContentDraftsPublic)
def read_drafts(
    session: SessionDep, membership: BrandMembership
) -> ContentDraftsPublic:
    drafts = session.exec(
        select(ContentDraft).where(ContentDraft.brand_id == membership.brand_id)
    ).all()
    drafts = sorted(drafts, key=lambda draft: draft.created_at, reverse=True)
    data = [_public(draft) for draft in drafts]
    return ContentDraftsPublic(data=data, count=len(data))


@router.get("/{draft_id}", response_model=ContentDraftDetail)
def read_draft(
    session: SessionDep, membership: BrandMembership, draft_id: uuid.UUID
) -> ContentDraftDetail:
    return _detail(session, get_draft_or_404(session, membership.brand_id, draft_id))


@router.patch("/{draft_id}", response_model=ContentDraftDetail)
def update_draft(
    *,
    session: SessionDep,
    membership: BrandMembership,
    draft_id: uuid.UUID,
    draft_in: ContentDraftUpdate,
) -> ContentDraftDetail:
    draft = get_draft_or_404(session, membership.brand_id, draft_id)
    if draft.status in {DraftStatus.PUBLISHED.value, DraftStatus.PUBLISH_FAILED.value}:
        raise HTTPException(
            status_code=400, detail="Published or publish-failed drafts cannot be edited"
        )
    if draft_in.caption is not None:
        draft.caption = draft_in.caption
        draft.user_edited = True
    if draft_in.alternative_captions is not None:
        draft.alternative_captions_json = draft_in.alternative_captions
        draft.user_edited = True
    if draft_in.hashtags is not None:
        draft.hashtags = draft_in.hashtags
        draft.user_edited = True
    if draft_in.cta is not None:
        draft.cta = draft_in.cta
        draft.user_edited = True
    if draft.status == DraftStatus.APPROVED.value:
        draft.status = DraftStatus.NEEDS_APPROVAL.value
        draft.approved_by = None
        draft.approved_at = None
    draft.updated_at = datetime.now(UTC)
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return _detail(session, draft)


@router.post("/{draft_id}/generate-caption", response_model=ContentDraftDetail)
def generate_caption_endpoint(
    *,
    session: SessionDep,
    membership: BrandMembership,
    draft_id: uuid.UUID,
    request_in: CaptionGenerateRequest,
) -> ContentDraftDetail:
    draft = get_draft_or_404(session, membership.brand_id, draft_id)
    try:
        draft = generate_caption_for_draft(session, draft, force=request_in.force)
    except CaptionGenerationError as exc:
        status_code = 409 if (draft.user_edited and not request_in.force) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return _detail(session, draft)


@router.post("/{draft_id}/submit", response_model=ContentDraftDetail)
def submit_draft(
    session: SessionDep, membership: BrandMembership, draft_id: uuid.UUID
) -> ContentDraftDetail:
    draft = get_draft_or_404(session, membership.brand_id, draft_id)
    if draft.status not in {DraftStatus.DRAFT.value, DraftStatus.REJECTED.value}:
        raise HTTPException(
            status_code=400, detail="Only draft or rejected content can be submitted"
        )
    if not draft.caption.strip():
        raise HTTPException(status_code=400, detail="Add a caption before submitting")
    draft.status = DraftStatus.NEEDS_APPROVAL.value
    draft.updated_at = datetime.now(UTC)
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return _detail(session, draft)

