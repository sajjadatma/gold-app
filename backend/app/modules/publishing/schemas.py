import uuid
from datetime import datetime

from sqlmodel import SQLModel


class SocialConnectionUpdate(SQLModel):
    external_account_id: str | None = None
    account_name: str | None = None
    access_token: str | None = None
    token_expires_at: datetime | None = None


class SocialConnectionPublic(SQLModel):
    provider: str
    external_account_id: str | None
    account_name: str | None
    status: str
    token_expires_at: datetime | None
    updated_at: datetime | None


class PublishJobPublic(SQLModel):
    id: uuid.UUID
    draft_id: uuid.UUID
    provider: str
    status: str
    remote_post_id: str | None
    remote_post_url: str | None
    error_message: str | None
    attempt_count: int
    created_at: datetime
    updated_at: datetime


class PublishJobsPublic(SQLModel):
    data: list[PublishJobPublic]
    count: int
