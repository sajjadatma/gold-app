import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class BrandModelType(StrEnum):
    VIRTUAL = "virtual"
    REAL = "real"


class BrandModelStatus(StrEnum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    ARCHIVED = "archived"
    FAILED = "failed"


class BrandModel(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(foreign_key="brand.id", index=True, ondelete="CASCADE")
    type: str = Field(default=BrandModelType.VIRTUAL.value, max_length=32)
    name: str = Field(max_length=255)
    status: str = Field(default=BrandModelStatus.DRAFT.value, max_length=32)
    is_default: bool = Field(default=False)
    config_json: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class BrandModelReference(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_model_id: uuid.UUID = Field(
        foreign_key="brandmodel.id", index=True, ondelete="CASCADE"
    )
    storage_key: str = Field(unique=True, max_length=1024)
    content_type: str = Field(max_length=255)
    is_canonical: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow)


class ConsentRecord(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_model_id: uuid.UUID = Field(
        foreign_key="brandmodel.id", index=True, ondelete="CASCADE"
    )
    confirmed_by_user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    confirmation_text_version: str = Field(max_length=64)
    permission_scope: str = Field(max_length=128)
    confirmed_at: datetime = Field(default_factory=utcnow)
