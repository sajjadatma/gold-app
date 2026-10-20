import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Index, text
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class ConnectionStatus(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class PublishStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"


class SocialConnection(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(
        foreign_key="brand.id", unique=True, index=True, ondelete="CASCADE"
    )
    provider: str = Field(default="instagram", max_length=32)
    external_account_id: str | None = Field(default=None, max_length=255)
    account_name: str | None = Field(default=None, max_length=255)
    access_token: str | None = Field(default=None, max_length=4096)
    token_expires_at: datetime | None = None
    status: str = Field(default=ConnectionStatus.DISCONNECTED.value, max_length=32)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class PublishJob(SQLModel, table=True):
    __table_args__ = (
        Index(
            "uq_publishjob_active_draft",
            "draft_id",
            unique=True,
            postgresql_where=text("status <> 'failed'"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(foreign_key="brand.id", index=True, ondelete="CASCADE")
    draft_id: uuid.UUID = Field(foreign_key="contentdraft.id", index=True, ondelete="CASCADE")
    provider: str = Field(default="instagram", max_length=32)
    status: str = Field(default=PublishStatus.QUEUED.value, max_length=32)
    remote_post_id: str | None = Field(default=None, max_length=255)
    remote_post_url: str | None = Field(default=None, max_length=1024)
    error_message: str | None = Field(default=None, max_length=1000)
    attempt_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
