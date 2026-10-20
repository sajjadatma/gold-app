import uuid
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.modules.brand_import.models import BrandAsset, BrandImport
from app.modules.brand_import.schemas import (
    AssetsPublic,
    BrandAssetPublic,
    BrandImportDetail,
    BrandImportPublic,
    ImportsPublic,
)
from app.modules.brand_import.service import UploadedInput, process_import
from app.modules.brand_import.validation import limit_for
from app.modules.brands.deps import BrandMembership, BrandOwner
from app.providers.storage import StorageError, get_storage

router = APIRouter(prefix="/brands/{brand_id}", tags=["Brand Import"])


def _asset_public(asset: BrandAsset) -> BrandAssetPublic:
    return BrandAssetPublic(
        id=asset.id,
        asset_type=asset.asset_type,
        original_filename=asset.original_filename,
        content_type=asset.content_type,
        size_bytes=asset.size_bytes,
        checksum=asset.checksum,
        width=asset.width,
        height=asset.height,
        page_count=asset.page_count,
        processing_status=asset.processing_status,
        is_active=asset.is_active,
        created_at=asset.created_at,
    )


def _import_public(import_row: BrandImport) -> BrandImportPublic:
    return BrandImportPublic(
        id=import_row.id,
        status=import_row.status,
        uploaded_file_count=import_row.uploaded_file_count,
        processed_file_count=import_row.processed_file_count,
        error_count=import_row.error_count,
        created_at=import_row.created_at,
        updated_at=import_row.updated_at,
    )


def get_import_or_404(
    session: SessionDep, brand_id: uuid.UUID, import_id: uuid.UUID
) -> BrandImport:
    import_row = session.get(BrandImport, import_id)
    if not import_row or import_row.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Import not found")
    return import_row


def get_asset_or_404(
    session: SessionDep, brand_id: uuid.UUID, asset_id: uuid.UUID
) -> BrandAsset:
    asset = session.get(BrandAsset, asset_id)
    if not asset or asset.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("/imports", response_model=BrandImportDetail)
async def create_import(
    session: SessionDep,
    current_user: CurrentUser,
    membership: BrandMembership,
    files: Annotated[list[UploadFile], File(description="Brand files to import")],
) -> BrandImportDetail:
    if not files:
        raise HTTPException(status_code=422, detail="At least one file is required")
    import_row = BrandImport(
        brand_id=membership.brand_id,
        created_by=current_user.id,
    )
    session.add(import_row)
    session.commit()
    session.refresh(import_row)

    uploads: list[UploadedInput] = []
    for upload in files:
        filename = upload.filename or "upload"
        limit = limit_for(filename)
        data = await upload.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(
                status_code=413,
                detail=f"{filename} exceeds the {limit // (1024 * 1024)} MB limit",
            )
        uploads.append(
            UploadedInput(
                filename=filename,
                content_type=upload.content_type,
                data=data,
            )
        )

    process_import(session, import_row, uploads)
    assets = session.exec(
        select(BrandAsset).where(BrandAsset.import_id == import_row.id)
    ).all()
    return BrandImportDetail(
        **_import_public(import_row).model_dump(),
        assets=[_asset_public(asset) for asset in assets],
    )


@router.get("/imports", response_model=ImportsPublic)
def read_imports(session: SessionDep, membership: BrandMembership) -> ImportsPublic:
    imports = session.exec(
        select(BrandImport).where(BrandImport.brand_id == membership.brand_id)
    ).all()
    imports = sorted(imports, key=lambda row: row.created_at, reverse=True)
    data = [_import_public(import_row) for import_row in imports]
    return ImportsPublic(data=data, count=len(data))


@router.get("/imports/{import_id}", response_model=BrandImportDetail)
def read_import(
    session: SessionDep, membership: BrandMembership, import_id: uuid.UUID
) -> BrandImportDetail:
    import_row = get_import_or_404(session, membership.brand_id, import_id)
    assets = session.exec(
        select(BrandAsset).where(BrandAsset.import_id == import_row.id)
    ).all()
    return BrandImportDetail(
        **_import_public(import_row).model_dump(),
        assets=[_asset_public(asset) for asset in assets],
    )


@router.get("/assets", response_model=AssetsPublic)
def read_assets(
    session: SessionDep,
    membership: BrandMembership,
    asset_type: Annotated[str | None, Query()] = None,
    active_only: bool = True,
) -> AssetsPublic:
    statement = select(BrandAsset).where(BrandAsset.brand_id == membership.brand_id)
    if asset_type:
        statement = statement.where(BrandAsset.asset_type == asset_type)
    if active_only:
        statement = statement.where(BrandAsset.is_active.is_(True))  # type: ignore[attr-defined]
    assets = session.exec(statement).all()
    assets = sorted(assets, key=lambda asset: asset.created_at, reverse=True)
    data = [_asset_public(asset) for asset in assets]
    return AssetsPublic(data=data, count=len(data))


@router.delete("/assets/{asset_id}")
def archive_asset(
    session: SessionDep, owner: BrandOwner, asset_id: uuid.UUID
) -> dict[str, str]:
    asset = get_asset_or_404(session, owner.brand_id, asset_id)
    asset.is_active = False
    session.add(asset)
    session.commit()
    return {"message": "Asset removed from active use"}


@router.get("/assets/{asset_id}/download")
def download_asset(
    session: SessionDep, membership: BrandMembership, asset_id: uuid.UUID
) -> Response:
    asset = get_asset_or_404(session, membership.brand_id, asset_id)
    try:
        data = get_storage().read(asset.storage_key)
    except StorageError:
        raise HTTPException(status_code=404, detail="Asset object not found")
    filename = asset.original_filename.replace('"', "")
    return Response(
        content=data,
        media_type=asset.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/assets/{asset_id}/preview")
def preview_asset(
    session: SessionDep, membership: BrandMembership, asset_id: uuid.UUID
) -> Response:
    asset = get_asset_or_404(session, membership.brand_id, asset_id)
    if not (
        asset.content_type.startswith("image/")
        or asset.content_type == "application/pdf"
    ):
        raise HTTPException(status_code=415, detail="Preview is not available")
    try:
        data = get_storage().read(asset.storage_key)
    except StorageError:
        raise HTTPException(status_code=404, detail="Asset object not found")
    return Response(
        content=data,
        media_type=asset.content_type,
        headers={
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
            "Cache-Control": "private, max-age=300",
        },
    )
