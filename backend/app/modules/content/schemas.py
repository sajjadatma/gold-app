import uuid
from datetime import datetime
from typing import Any

from pydantic import Field as PydanticField
from sqlmodel import SQLModel


class ContentDraftCreate(SQLModel):
    generated_asset_id: uuid.UUID


class ContentDraftUpdate(SQLModel):
    caption: str | None = None
    alternative_captions: list[str] | None = None
    hashtags: str | None = None
    cta: str | None = None


class CaptionGenerateRequest(SQLModel):
    force: bool = False


class CaptionResult(SQLModel):
    primary_caption: str = PydanticField(min_length=1)
    alternatives: list[str] = PydanticField(min_length=2, max_length=3)
    cta: str | None = None
    hashtags: list[str] = PydanticField(default_factory=list)


class ContentDraftPublic(SQLModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    product_id: uuid.UUID
    generated_asset_id: uuid.UUID
    caption: str
    alternative_captions_json: list[str]
    hashtags: str
    cta: str | None
    status: str
    created_by: uuid.UUID
    approved_by: uuid.UUID | None
    approved_at: datetime | None
    user_edited: bool
    created_at: datetime
    updated_at: datetime


class ContentDraftDetail(ContentDraftPublic):
    generation_request_id: uuid.UUID
    integrity_status: str
    integrity_findings_json: dict[str, Any]
    product_name: str
    product_category: str
    brand_profile_version: int
    model_name: str | None


class ContentDraftsPublic(SQLModel):
    data: list[ContentDraftPublic]
    count: int
