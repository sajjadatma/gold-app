import uuid

from fastapi import APIRouter, HTTPException, Response

from app.api.deps import SessionDep
from app.modules.brand_import.models import BrandAsset
from app.modules.brands.deps import BrandMembership
from app.providers.storage import StorageError, get_storage

router = APIRouter(prefix="/brands/{brand_id}", tags=["Brand Assets"])


def get_asset_or_404(
    session: SessionDep, brand_id: uuid.UUID, asset_id: uuid.UUID
) -> BrandAsset:
    asset = session.get(BrandAsset, asset_id)
    if not asset or asset.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


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
