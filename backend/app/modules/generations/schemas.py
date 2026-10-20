import uuid
from datetime import datetime
from typing import Any, Literal

from sqlmodel import SQLModel


class GenerationCreate(SQLModel):
    product_id: uuid.UUID
    mode: Literal["studio", "on_model", "campaign"] = "studio"
    aspect_ratio: Literal["1:1", "4:5", "9:16", "16:9"] = "4:5"
    brand_model_id: uuid.UUID | None = None
    source_image_id: uuid.UUID | None = None
    style_notes: str = ""


class GeneratedAssetPublic(SQLModel):
    id: uuid.UUID
    content_type: str
    width: int | None
    height: int | None
    integrity_status: str
    integrity_findings_json: dict[str, Any]
    created_at: datetime


class GenerationPublic(SQLModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    product_id: uuid.UUID
    brand_profile_id: uuid.UUID
    brand_model_id: uuid.UUID | None
    mode: str
    aspect_ratio: str
    status: str
    provider: str
    model: str | None
    prompt_version: str
    parameters_json: dict[str, Any]
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class GenerationDetail(GenerationPublic):
    assets: list[GeneratedAssetPublic]


class GenerationsPublic(SQLModel):
    data: list[GenerationPublic]
    count: int
