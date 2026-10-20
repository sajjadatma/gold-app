import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from sqlmodel import select

from app.api.deps import SessionDep
from app.core.config import settings
from app.modules.brand_import.validation import ValidationError, validate_upload
from app.modules.brand_models.models import (
    BrandModel,
    BrandModelReference,
    BrandModelStatus,
    BrandModelType,
    ConsentRecord,
)
from app.modules.brand_models.schemas import (
    BrandModelCreate,
    BrandModelDetail,
    BrandModelPublic,
    BrandModelsPublic,
    BrandModelUpdate,
    CanonicalReferenceUpdate,
    ConsentCreate,
    ConsentPublic,
    ModelReferencePublic,
)
from app.modules.brands.deps import BrandMembership
from app.providers.ai import generate_model_previews
from app.providers.storage import build_storage_key, get_storage

router = APIRouter(prefix="/brands/{brand_id}/models", tags=["Brand Models"])


def _model_public(model: BrandModel) -> BrandModelPublic:
    return BrandModelPublic(
        id=model.id,
        brand_id=model.brand_id,
        type=model.type,
        name=model.name,
        status=model.status,
        is_default=model.is_default,
        config_json=model.config_json,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _reference_public(reference: BrandModelReference) -> ModelReferencePublic:
    return ModelReferencePublic(
        id=reference.id,
        content_type=reference.content_type,
        is_canonical=reference.is_canonical,
        created_at=reference.created_at,
    )


def _consent_public(consent: ConsentRecord | None) -> ConsentPublic | None:
    if not consent:
        return None
    return ConsentPublic(
        id=consent.id,
        confirmed_by_user_id=consent.confirmed_by_user_id,
        confirmation_text_version=consent.confirmation_text_version,
        permission_scope=consent.permission_scope,
        confirmed_at=consent.confirmed_at,
    )


def get_model_or_404(
    session: SessionDep, brand_id: uuid.UUID, model_id: uuid.UUID
) -> BrandModel:
    model = session.get(BrandModel, model_id)
    if not model or model.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Brand model not found")
    return model


def _latest_consent(
    session: SessionDep, model_id: uuid.UUID
) -> ConsentRecord | None:
    records = session.exec(
        select(ConsentRecord).where(ConsentRecord.brand_model_id == model_id)
    ).all()
    return max(records, key=lambda record: record.confirmed_at, default=None)


def _references(
    session: SessionDep, model_id: uuid.UUID
) -> list[BrandModelReference]:
    references = session.exec(
        select(BrandModelReference).where(
            BrandModelReference.brand_model_id == model_id
        )
    ).all()
    return sorted(references, key=lambda reference: reference.created_at)


def _detail(session: SessionDep, model: BrandModel) -> BrandModelDetail:
    return BrandModelDetail(
        **_model_public(model).model_dump(),
        references=[_reference_public(item) for item in _references(session, model.id)],
        consent=_consent_public(_latest_consent(session, model.id)),
    )


@router.get("", response_model=BrandModelsPublic)
def read_models(
    session: SessionDep, membership: BrandMembership
) -> BrandModelsPublic:
    models = session.exec(
        select(BrandModel).where(BrandModel.brand_id == membership.brand_id)
    ).all()
    models = sorted(models, key=lambda model: model.created_at, reverse=True)
    data = [_model_public(model) for model in models]
    return BrandModelsPublic(data=data, count=len(data))


@router.post("", response_model=BrandModelDetail)
def create_model(
    *, session: SessionDep, membership: BrandMembership, model_in: BrandModelCreate
) -> BrandModelDetail:
    if not model_in.name.strip():
        raise HTTPException(status_code=422, detail="Model name is required")
    model = BrandModel(
        brand_id=membership.brand_id,
        type=model_in.type,
        name=model_in.name.strip(),
        status=BrandModelStatus.DRAFT.value,
        config_json=model_in.config_json,
    )
    session.add(model)
    session.commit()
    session.refresh(model)
    return _detail(session, model)


@router.get("/{model_id}", response_model=BrandModelDetail)
def read_model(
    session: SessionDep, membership: BrandMembership, model_id: uuid.UUID
) -> BrandModelDetail:
    return _detail(session, get_model_or_404(session, membership.brand_id, model_id))


@router.patch("/{model_id}", response_model=BrandModelDetail)
def update_model(
    *,
    session: SessionDep,
    membership: BrandMembership,
    model_id: uuid.UUID,
    model_in: BrandModelUpdate,
) -> BrandModelDetail:
    model = get_model_or_404(session, membership.brand_id, model_id)
    if model_in.name is not None:
        if not model_in.name.strip():
            raise HTTPException(status_code=422, detail="Model name is required")
        model.name = model_in.name.strip()
    if model_in.config_json is not None:
        model.config_json = model_in.config_json
    if model_in.status == "archived":
        model.status = BrandModelStatus.ARCHIVED.value
        model.is_default = False
    model.updated_at = datetime.now(UTC)
    session.add(model)
    session.commit()
    session.refresh(model)
    return _detail(session, model)


@router.post("/{model_id}/references", response_model=BrandModelDetail)
async def upload_reference(
    session: SessionDep,
    membership: BrandMembership,
    model_id: uuid.UUID,
    file: UploadFile = File(...),
) -> BrandModelDetail:
    model = get_model_or_404(session, membership.brand_id, model_id)
    data = await file.read(settings.MAX_IMAGE_BYTES + 1)
    if len(data) > settings.MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the size limit")
    try:
        validated = validate_upload(file.filename or "reference.png", file.content_type, data)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not validated.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Reference must be an image")
    if validated.extension == ".svg":
        raise HTTPException(status_code=400, detail="Reference must be a raster image")

    key = build_storage_key(
        membership.brand_id, f"models/{model_id}", validated.filename
    )
    stored = get_storage().save(key, validated.data, validated.content_type)
    has_canonical = any(
        reference.is_canonical for reference in _references(session, model_id)
    )
    reference = BrandModelReference(
        brand_model_id=model_id,
        storage_key=key,
        content_type=stored.content_type,
    )
    reference.is_canonical = not has_canonical
    session.add(reference)
    model.updated_at = datetime.now(UTC)
    session.add(model)
    session.commit()
    session.refresh(model)
    return _detail(session, model)


@router.post("/{model_id}/generate-previews", response_model=BrandModelDetail)
def generate_previews(
    session: SessionDep, membership: BrandMembership, model_id: uuid.UUID
) -> BrandModelDetail:
    model = get_model_or_404(session, membership.brand_id, model_id)
    if model.type != BrandModelType.VIRTUAL.value:
        raise HTTPException(
            status_code=400, detail="Preview generation is only for virtual models"
        )
    model.status = BrandModelStatus.GENERATING.value
    model.updated_at = datetime.now(UTC)
    session.add(model)
    session.commit()

    try:
        images = generate_model_previews(model.name, model.config_json, count=3)
        existing = _references(session, model_id)
        for index, data in enumerate(images):
            key = build_storage_key(
                membership.brand_id, f"models/{model_id}", f"preview-{index}.png"
            )
            stored = get_storage().save(key, data, "image/png")
            reference = BrandModelReference(
                brand_model_id=model_id,
                storage_key=key,
                content_type=stored.content_type,
                is_canonical=not existing and index == 0,
            )
            session.add(reference)
        model.status = BrandModelStatus.READY.value
        model.updated_at = datetime.now(UTC)
        session.add(model)
        session.commit()
        session.refresh(model)
    except Exception as exc:  # noqa: BLE001
        model.status = BrandModelStatus.FAILED.value
        model.updated_at = datetime.now(UTC)
        session.add(model)
        session.commit()
        raise HTTPException(
            status_code=502, detail="Preview generation failed. Please retry."
        ) from exc
    return _detail(session, model)


@router.post("/{model_id}/canonical", response_model=BrandModelDetail)
def set_canonical_reference(
    *,
    session: SessionDep,
    membership: BrandMembership,
    model_id: uuid.UUID,
    reference_in: CanonicalReferenceUpdate,
) -> BrandModelDetail:
    model = get_model_or_404(session, membership.brand_id, model_id)
    references = _references(session, model_id)
    target = next(
        (item for item in references if item.id == reference_in.reference_id), None
    )
    if not target:
        raise HTTPException(status_code=404, detail="Reference not found")
    for reference in references:
        reference.is_canonical = reference.id == target.id
        session.add(reference)
    model.updated_at = datetime.now(UTC)
    session.add(model)
    session.commit()
    session.refresh(model)
    return _detail(session, model)


@router.post("/{model_id}/consent", response_model=BrandModelDetail)
def record_consent(
    *,
    session: SessionDep,
    membership: BrandMembership,
    model_id: uuid.UUID,
    consent_in: ConsentCreate,
) -> BrandModelDetail:
    model = get_model_or_404(session, membership.brand_id, model_id)
    if model.type != BrandModelType.REAL.value:
        raise HTTPException(
            status_code=400, detail="Consent records apply only to real models"
        )
    if not _references(session, model_id):
        raise HTTPException(
            status_code=400, detail="Upload at least one reference photo first"
        )
    consent = ConsentRecord(
        brand_model_id=model_id,
        confirmed_by_user_id=membership.user_id,
        confirmation_text_version=consent_in.confirmation_text_version,
        permission_scope=consent_in.permission_scope,
    )
    session.add(consent)
    model.status = BrandModelStatus.READY.value
    model.updated_at = datetime.now(UTC)
    session.add(model)
    session.commit()
    session.refresh(model)
    return _detail(session, model)


@router.post("/{model_id}/default", response_model=BrandModelDetail)
def set_default_model(
    session: SessionDep, membership: BrandMembership, model_id: uuid.UUID
) -> BrandModelDetail:
    model = get_model_or_404(session, membership.brand_id, model_id)
    if model.status != BrandModelStatus.READY.value:
        raise HTTPException(status_code=400, detail="Only ready models can be default")
    if model.type == BrandModelType.REAL.value and not _latest_consent(
        session, model_id
    ):
        raise HTTPException(
            status_code=400, detail="A real model needs a consent record first"
        )
    other_models = session.exec(
        select(BrandModel).where(
            BrandModel.brand_id == membership.brand_id,
            BrandModel.is_default.is_(True),  # type: ignore[attr-defined]
        )
    ).all()
    for other in other_models:
        other.is_default = False
        session.add(other)
    model.is_default = True
    model.updated_at = datetime.now(UTC)
    session.add(model)
    session.commit()
    session.refresh(model)
    return _detail(session, model)


@router.get("/{model_id}/references/{reference_id}/download")
def download_reference(
    session: SessionDep,
    membership: BrandMembership,
    model_id: uuid.UUID,
    reference_id: uuid.UUID,
) -> Response:
    model = get_model_or_404(session, membership.brand_id, model_id)
    reference = session.get(BrandModelReference, reference_id)
    if not reference or reference.brand_model_id != model.id:
        raise HTTPException(status_code=404, detail="Reference not found")
    try:
        data = get_storage().read(reference.storage_key)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail="Reference object not found") from exc
    return Response(
        content=data,
        media_type=reference.content_type,
        headers={
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=300",
        },
    )
