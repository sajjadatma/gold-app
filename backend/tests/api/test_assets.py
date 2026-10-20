import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.modules.brand_import.models import BrandAsset, BrandImport, ImportStatus
from app.providers.storage import build_storage_key, get_storage
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def _create_brand(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        f"{settings.API_V1_STR}/brands", headers=headers, json={"name": "Storage Test"}
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _create_stored_asset(db: Session, brand_id: str, user_id: uuid.UUID) -> BrandAsset:
    brand_uuid = uuid.UUID(brand_id)
    import_row = BrandImport(
        brand_id=brand_uuid,
        status=ImportStatus.COMPLETED.value,
        created_by=user_id,
    )
    db.add(import_row)
    db.flush()
    key = build_storage_key(brand_uuid, "assets", "brand.pdf")
    data = b"%PDF-1.4 private brand book"
    stored = get_storage().save(key, data, "application/pdf")
    asset = BrandAsset(
        brand_id=brand_uuid,
        import_id=import_row.id,
        original_filename="brand.pdf",
        storage_key=key,
        content_type="application/pdf",
        size_bytes=stored.size_bytes,
        checksum=stored.checksum,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def test_member_can_download_private_asset(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _create_brand(client, normal_user_token_headers)
    me = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers).json()
    asset = _create_stored_asset(db, brand_id, uuid.UUID(me["id"]))

    response = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/assets/{asset.id}/download",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-1.4")
    assert response.headers["content-disposition"].startswith("attachment;")


def test_unrelated_user_cannot_download_asset(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _create_brand(client, normal_user_token_headers)
    me = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers).json()
    asset = _create_stored_asset(db, brand_id, uuid.UUID(me["id"]))

    other_headers = authentication_token_from_email(
        client=client, email=random_email(), db=db
    )
    response = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/assets/{asset.id}/download",
        headers=other_headers,
    )
    assert response.status_code == 404


def test_superuser_cannot_bypass_tenant_asset_isolation(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    brand_id = _create_brand(client, normal_user_token_headers)
    me = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers).json()
    asset = _create_stored_asset(db, brand_id, uuid.UUID(me["id"]))

    response = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/assets/{asset.id}/download",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_asset_requires_authentication(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _create_brand(client, normal_user_token_headers)
    me = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers).json()
    asset = _create_stored_asset(db, brand_id, uuid.UUID(me["id"]))
    response = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/assets/{asset.id}/download"
    )
    assert response.status_code == 401
