import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column, Index, text
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class ImportStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    COMPLETED = "completed"
    FAILED = "failed"


class AssetType(StrEnum):
    BRAND_BOOK = "brand_book"
    LOGO = "logo"
    FONT = "font"
    IMAGE = "image"
    CAMPAIGN_REFERENCE = "campaign_reference"
    PATTERN = "pattern"
    GRAPHIC_ELEMENT = "graphic_element"
    DESIGN_SOURCE = "design_source"
    OTHER = "other"


class ProcessingStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    STORED = "stored"
    FAILED = "failed"


class BrandImport(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(foreign_key="brand.id", index=True, ondelete="CASCADE")
    status: str = Field(default=ImportStatus.PENDING.value, max_length=32)
    uploaded_file_count: int = Field(default=0)
    processed_file_count: int = Field(default=0)
    error_count: int = Field(default=0)
    created_by: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class BrandAsset(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(foreign_key="brand.id", index=True, ondelete="CASCADE")
    import_id: uuid.UUID = Field(
        foreign_key="brandimport.id", index=True, ondelete="CASCADE"
    )
    asset_type: str = Field(default=AssetType.OTHER.value, max_length=32)
    original_filename: str = Field(max_length=512)
    storage_key: str = Field(unique=True, index=True, max_length=1024)
    content_type: str = Field(max_length=255)
    size_bytes: int
    checksum: str = Field(max_length=128)
    width: int | None = None
    height: int | None = None
    page_count: int | None = None
    metadata_json: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    processing_status: str = Field(
        default=ProcessingStatus.STORED.value, max_length=32
    )
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class ProfileStatus(StrEnum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    ACTIVE = "active"
    ARCHIVED = "archived"


class BrandProfile(SQLModel, table=True):
    __table_args__ = (
        Index(
            "uq_brandprofile_one_active",
            "brand_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(foreign_key="brand.id", index=True, ondelete="CASCADE")
    version: int = 1
    status: str = Field(default=ProfileStatus.DRAFT.value, max_length=32)
    profile_json: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    created_from_import_id: uuid.UUID | None = Field(
        default=None, foreign_key="brandimport.id", ondelete="SET NULL"
    )
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    activated_at: datetime | None = None
