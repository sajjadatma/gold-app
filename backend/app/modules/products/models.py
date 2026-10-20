import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class ProductCategory(StrEnum):
    RING = "ring"
    NECKLACE = "necklace"
    BRACELET = "bracelet"
    EARRINGS = "earrings"
    SET = "set"
    PENDANT = "pendant"
    OTHER = "other"


class ProductStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class QualityStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    BLOCKED = "blocked"


class Product(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(foreign_key="brand.id", index=True, ondelete="CASCADE")
    name: str = Field(max_length=255)
    sku: str | None = Field(default=None, max_length=128)
    category: str = Field(default=ProductCategory.OTHER.value, max_length=32)
    metal_type: str | None = Field(default=None, max_length=128)
    metal_color: str | None = Field(default=None, max_length=128)
    stone_type: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
    integrity_notes: str | None = Field(default=None, max_length=2000)
    status: str = Field(default=ProductStatus.ACTIVE.value, max_length=32)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class ProductImage(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    product_id: uuid.UUID = Field(
        foreign_key="product.id", index=True, ondelete="CASCADE"
    )
    storage_key: str = Field(unique=True, max_length=1024)
    content_type: str = Field(max_length=255)
    width: int | None = None
    height: int | None = None
    is_primary: bool = Field(default=False)
    quality_status: str = Field(default=QualityStatus.OK.value, max_length=32)
    quality_findings_json: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    created_at: datetime = Field(default_factory=utcnow)
