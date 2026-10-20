import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Response
from sqlmodel import select

from app.api.deps import SessionDep
from app.modules.brand_import.models import BrandProfile, ProfileStatus
from app.modules.brand_models.models import BrandModel, BrandModelStatus
from app.modules.brands.deps import BrandMembership
from app.modules.generations.models import (
    GeneratedAsset,
    GenerationRequest,
    GenerationStatus,
)
from app.modules.generations.schemas import (
    GeneratedAssetPublic,
    GenerationCreate,
    GenerationDetail,
    GenerationPublic,
    GenerationsPublic,
)
from app.modules.generations.service import GenerationError
from app.modules.products.models import Product, ProductImage, ProductStatus
from app.providers.storage import get_storage
from app.workers.tasks import enqueue_generation

router = APIRouter(prefix="/brands/{brand_id}/generations", tags=["Generations"])


def _asset_public(asset: GeneratedAsset) -> GeneratedAssetPublic:
    return GeneratedAssetPublic(
        id=asset.id,
        content_type=asset.content_type,
        width=asset.width,
        height=asset.height,
        integrity_status=asset.integrity_status,
        integrity_findings_json=asset.integrity_findings_json,
        created_at=asset.created_at,
    )


def _request_public(request: GenerationRequest) -> GenerationPublic:
    return GenerationPublic(
        id=request.id,
        brand_id=request.brand_id,
        product_id=request.product_id,
        brand_profile_id=request.brand_profile_id,
        brand_model_id=request.brand_model_id,
        mode=request.mode,
        aspect_ratio=request.aspect_ratio,
        status=request.status,
        provider=request.provider,
        model=request.model,
        prompt_version=request.prompt_version,
        parameters_json=request.parameters_json,
        error_message=request.error_message,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


def _detail(session: SessionDep, request: GenerationRequest) -> GenerationDetail:
    assets = session.exec(
        select(GeneratedAsset).where(
            GeneratedAsset.generation_request_id == request.id
        )
    ).all()
    assets = sorted(assets, key=lambda asset: asset.created_at)
    return GenerationDetail(
        **_request_public(request).model_dump(),
        assets=[_asset_public(asset) for asset in assets],
    )


def get_request_or_404(
    session: SessionDep, brand_id: uuid.UUID, request_id: uuid.UUID
) -> GenerationRequest:
    request = session.get(GenerationRequest, request_id)
    if not request or request.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Generation not found")
    return request


@router.post("", response_model=GenerationDetail)
async def create_generation(
    *, session: SessionDep, membership: BrandMembership, request_in: GenerationCreate
) -> GenerationDetail:
    profile = session.exec(
        select(BrandProfile).where(
            BrandProfile.brand_id == membership.brand_id,
            BrandProfile.status == ProfileStatus.ACTIVE.value,
        )
    ).first()
    if not profile:
        raise HTTPException(
            status_code=400, detail="Activate a brand profile before generating"
        )

    product = session.get(Product, request_in.product_id)
    if (
        not product
        or product.brand_id != membership.brand_id
        or product.status != ProductStatus.ACTIVE.value
    ):
        raise HTTPException(status_code=404, detail="Product not found")
    images = session.exec(
        select(ProductImage).where(ProductImage.product_id == product.id)
    ).all()
    if not images:
        raise HTTPException(
            status_code=400, detail="Add a source product image before generating"
        )
    if request_in.source_image_id and not any(
        image.id == request_in.source_image_id for image in images
    ):
        raise HTTPException(status_code=400, detail="Source image not found")

    model: BrandModel | None = None
    if request_in.brand_model_id:
        model = session.get(BrandModel, request_in.brand_model_id)
        if not model or model.brand_id != membership.brand_id:
            raise HTTPException(status_code=404, detail="Brand model not found")
        if model.status != BrandModelStatus.READY.value:
            raise HTTPException(status_code=400, detail="Brand model is not ready")
    if request_in.mode == "on_model" and not model:
        raise HTTPException(status_code=400, detail="On-model mode requires a brand model")

    request = GenerationRequest(
        brand_id=membership.brand_id,
        product_id=product.id,
        brand_profile_id=profile.id,
        brand_model_id=model.id if model else None,
        mode=request_in.mode,
        aspect_ratio=request_in.aspect_ratio,
        status=GenerationStatus.QUEUED.value,
        parameters_json={
            "source_image_id": str(request_in.source_image_id or ""),
            "style_notes": request_in.style_notes[:500],
        },
    )
    session.add(request)
    session.commit()
    session.refresh(request)

    try:
        await enqueue_generation(request.id)
    except GenerationError:
        # The persisted request carries the user-visible failure state.
        pass
    session.expire_all()
    refreshed = session.get(GenerationRequest, request.id)
    if not refreshed:
        raise HTTPException(status_code=500, detail="Generation request lost")
    return _detail(session, refreshed)


@router.get("", response_model=GenerationsPublic)
def read_generations(
    session: SessionDep, membership: BrandMembership
) -> GenerationsPublic:
    requests = session.exec(
        select(GenerationRequest).where(
            GenerationRequest.brand_id == membership.brand_id
        )
    ).all()
    requests = sorted(requests, key=lambda request: request.created_at, reverse=True)
    data = [_request_public(request) for request in requests]
    return GenerationsPublic(data=data, count=len(data))


@router.get("/{request_id}", response_model=GenerationDetail)
def read_generation(
    session: SessionDep, membership: BrandMembership, request_id: uuid.UUID
) -> GenerationDetail:
    return _detail(session, get_request_or_404(session, membership.brand_id, request_id))


@router.post("/{request_id}/retry", response_model=GenerationDetail)
async def retry_generation(
    session: SessionDep, membership: BrandMembership, request_id: uuid.UUID
) -> GenerationDetail:
    request = get_request_or_404(session, membership.brand_id, request_id)
    if request.status != GenerationStatus.FAILED.value:
        raise HTTPException(status_code=400, detail="Only failed generations can retry")
    request.status = GenerationStatus.QUEUED.value
    request.error_message = None
    request.updated_at = datetime.now(UTC)
    session.add(request)
    session.commit()
    try:
        await enqueue_generation(request.id)
    except GenerationError:
        pass
    session.expire_all()
    refreshed = session.get(GenerationRequest, request.id)
    if not refreshed:
        raise HTTPException(status_code=500, detail="Generation request lost")
    return _detail(session, refreshed)


@router.get("/assets/{asset_id}/download")
def download_generated_asset(
    session: SessionDep, membership: BrandMembership, asset_id: uuid.UUID
) -> Response:
    asset = session.get(GeneratedAsset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Generated asset not found")
    request = session.get(GenerationRequest, asset.generation_request_id)
    if not request or request.brand_id != membership.brand_id:
        raise HTTPException(status_code=404, detail="Generated asset not found")
    try:
        data = get_storage().read(asset.storage_key)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail="Generated object not found") from exc
    return Response(
        content=data,
        media_type=asset.content_type,
        headers={
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=300",
        },
    )
