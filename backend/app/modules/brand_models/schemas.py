import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import Field
from sqlmodel import SQLModel


class BrandModelCreate(SQLModel):
    type: Literal["virtual", "real"]
    name: str
    config_json: dict[str, Any] = Field(default_factory=dict)


class BrandModelUpdate(SQLModel):
    name: str | None = None
    config_json: dict[str, Any] | None = None
    status: Literal["archived"] | None = None


class ModelReferencePublic(SQLModel):
    id: uuid.UUID
    content_type: str
    is_canonical: bool
    created_at: datetime


class ConsentPublic(SQLModel):
    id: uuid.UUID
    confirmed_by_user_id: uuid.UUID
    confirmation_text_version: str
    permission_scope: str
    confirmed_at: datetime


class BrandModelPublic(SQLModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    type: str
    name: str
    status: str
    is_default: bool
    config_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class BrandModelDetail(BrandModelPublic):
    references: list[ModelReferencePublic]
    consent: ConsentPublic | None


class BrandModelsPublic(SQLModel):
    data: list[BrandModelPublic]
    count: int


class ConsentCreate(SQLModel):
    confirmation_text_version: str
    permission_scope: str


class CanonicalReferenceUpdate(SQLModel):
    reference_id: uuid.UUID
