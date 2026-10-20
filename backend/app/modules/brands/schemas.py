import uuid
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import SQLModel

from app.modules.brands.models import MemberRole


class BrandCreate(SQLModel):
    name: str


class BrandPublic(SQLModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str
    role: MemberRole
    created_at: datetime
    updated_at: datetime


class BrandsPublic(SQLModel):
    data: list[BrandPublic]
    count: int


class MemberPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: MemberRole
    created_at: datetime


class MembersPublic(SQLModel):
    data: list[MemberPublic]
    count: int


class MemberCreate(SQLModel):
    email: EmailStr
    role: MemberRole = MemberRole.CONTENT_MANAGER


class MemberUpdate(SQLModel):
    role: MemberRole
