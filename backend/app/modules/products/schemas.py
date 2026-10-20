import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel

from app.modules.products.models import ProductCategory


class ProductCreate(SQLModel):
    name: str
    category: ProductCategory
    sku: str | None = None
    metal_type: str | None = None
    metal_color: str | None = None
    stone_type: str | None = None
    description: str | None = None
    integrity_notes: str | None = None


class ProductUpdate(SQLModel):
    name: str | None = None
    category: ProductCategory | None = None
    sku: str | None = None
    metal_type: str | None = None
    metal_color: str | None = None
    stone_type: str | None = None
    description: str | None = None
    integrity_notes: str | None = None


class ProductImagePublic(SQLModel):
    id: uuid.UUID
    content_type: str
    width: int | None
    height: int | None
    is_primary: bool
    quality_status: str
    quality_findings_json: dict[str, Any]
    created_at: datetime


class ProductPublic(SQLModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    name: str
    sku: str | None
    category: str
    metal_type: str | None
    metal_color: str | None
    stone_type: str | None
    description: str | None
    integrity_notes: str | None
    status: str
    images: list[ProductImagePublic]
    created_at: datetime
    updated_at: datetime


class ProductsPublic(SQLModel):
    data: list[ProductPublic]
    count: int
