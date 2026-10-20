import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class GenerationMode(StrEnum):
    STUDIO = "studio"
    ON_MODEL = "on_model"
    CAMPAIGN = "campaign"


class GenerationStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IntegrityStatus(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class GenerationRequest(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(foreign_key="brand.id", index=True, ondelete="CASCADE")
    product_id: uuid.UUID = Field(foreign_key="product.id", ondelete="CASCADE")
    brand_profile_id: uuid.UUID = Field(foreign_key="brandprofile.id")
    brand_model_id: uuid.UUID | None = Field(
        default=None, foreign_key="brandmodel.id", ondelete="SET NULL"
    )
    mode: str = Field(default=GenerationMode.STUDIO.value, max_length=32)
    aspect_ratio: str = Field(default="4:5", max_length=16)
    status: str = Field(default=GenerationStatus.QUEUED.value, max_length=32)
    provider: str = Field(default="fake", max_length=64)
    model: str | None = Field(default=None, max_length=128)
    prompt_version: str = Field(default="mvp1", max_length=64)
    parameters_json: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    error_message: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class GeneratedAsset(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    generation_request_id: uuid.UUID = Field(
        foreign_key="generationrequest.id", index=True, ondelete="CASCADE"
    )
    storage_key: str = Field(unique=True, max_length=1024)
    content_type: str = Field(max_length=255)
    width: int | None = None
    height: int | None = None
    integrity_status: str = Field(
        default=IntegrityStatus.PENDING.value, max_length=32
    )
    integrity_findings_json: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    created_at: datetime = Field(default_factory=utcnow)
