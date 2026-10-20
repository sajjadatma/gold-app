import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class DraftStatus(StrEnum):
    DRAFT = "draft"
    NEEDS_APPROVAL = "needs_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    PUBLISH_FAILED = "publish_failed"


class ContentDraft(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(foreign_key="brand.id", index=True, ondelete="CASCADE")
    product_id: uuid.UUID = Field(foreign_key="product.id", ondelete="CASCADE")
    generated_asset_id: uuid.UUID = Field(
        foreign_key="generatedasset.id", ondelete="CASCADE"
    )
    caption: str = Field(default="", max_length=4000)
    alternative_captions_json: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    hashtags: str = Field(default="", max_length=2000)
    cta: str | None = Field(default=None, max_length=500)
    status: str = Field(default=DraftStatus.DRAFT.value, max_length=32)
    created_by: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    approved_by: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL"
    )
    approved_at: datetime | None = None
    user_edited: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
