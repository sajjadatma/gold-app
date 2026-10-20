import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel


class BrandAssetPublic(SQLModel):
    id: uuid.UUID
    asset_type: str
    original_filename: str
    content_type: str
    size_bytes: int
    checksum: str
    width: int | None
    height: int | None
    page_count: int | None
    processing_status: str
    is_active: bool
    created_at: datetime


class AssetsPublic(SQLModel):
    data: list[BrandAssetPublic]
    count: int


class BrandImportPublic(SQLModel):
    id: uuid.UUID
    status: str
    uploaded_file_count: int
    processed_file_count: int
    error_count: int
    created_at: datetime
    updated_at: datetime


class BrandImportDetail(BrandImportPublic):
    assets: list[BrandAssetPublic]


class ImportsPublic(SQLModel):
    data: list[BrandImportPublic]
    count: int


class BrandProfilePublic(SQLModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    version: int
    status: str
    profile_json: dict[str, Any]
    created_from_import_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    activated_at: datetime | None


class ProfilesPublic(SQLModel):
    data: list[BrandProfilePublic]
    count: int


class ProfileUpdate(SQLModel):
    profile_json: dict[str, Any]
