import re
import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import User
from app.modules.brands.deps import BrandMembership, BrandOwner
from app.modules.brands.models import Brand, BrandStatus, MemberRole, Membership
from app.modules.brands.schemas import (
    BrandCreate,
    BrandPublic,
    BrandsPublic,
    MemberCreate,
    MemberPublic,
    MembersPublic,
    MemberUpdate,
)

router = APIRouter(prefix="/brands", tags=["Brands"])


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60] or "brand"
    return f"{base}-{uuid.uuid4().hex[:6]}"


def _brand_public(brand: Brand, role: str) -> BrandPublic:
    return BrandPublic(
        id=brand.id,
        name=brand.name,
        slug=brand.slug,
        status=brand.status,
        role=MemberRole(role),
        created_at=brand.created_at,
        updated_at=brand.updated_at,
    )


@router.get("", response_model=BrandsPublic)
def read_brands(session: SessionDep, current_user: CurrentUser) -> BrandsPublic:
    memberships = session.exec(
        select(Membership).where(Membership.user_id == current_user.id)
    ).all()
    pairs: list[tuple[Brand, Membership]] = []
    for membership in memberships:
        brand = session.get(Brand, membership.brand_id)
        if brand:
            pairs.append((brand, membership))
    pairs.sort(key=lambda pair: pair[0].created_at)
    data = [_brand_public(brand, membership.role) for brand, membership in pairs]
    return BrandsPublic(data=data, count=len(data))


@router.post("", response_model=BrandPublic)
def create_brand(
    *, session: SessionDep, current_user: CurrentUser, brand_in: BrandCreate
) -> BrandPublic:
    name = brand_in.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Brand name is required")
    brand = Brand(name=name, slug=_slugify(name), status=BrandStatus.ACTIVE.value)
    session.add(brand)
    session.flush()
    membership = Membership(
        user_id=current_user.id,
        brand_id=brand.id,
        role=MemberRole.OWNER.value,
    )
    session.add(membership)
    session.commit()
    session.refresh(brand)
    return _brand_public(brand, membership.role)


@router.get("/{brand_id}", response_model=BrandPublic)
def read_brand(
    session: SessionDep, membership: BrandMembership
) -> BrandPublic:
    brand = session.get(Brand, membership.brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return _brand_public(brand, membership.role)


@router.get("/{brand_id}/members", response_model=MembersPublic)
def read_members(session: SessionDep, membership: BrandMembership) -> MembersPublic:
    members = session.exec(
        select(Membership).where(Membership.brand_id == membership.brand_id)
    ).all()
    members = sorted(members, key=lambda member: member.created_at)
    data: list[MemberPublic] = []
    for member in members:
        user = session.get(User, member.user_id)
        if not user:
            continue
        data.append(
            MemberPublic(
                id=member.id,
                user_id=member.user_id,
                email=user.email,
                full_name=user.full_name,
                role=MemberRole(member.role),
                created_at=member.created_at,
            )
        )
    return MembersPublic(data=data, count=len(data))


@router.post("/{brand_id}/members", response_model=MemberPublic)
def add_member(
    *,
    session: SessionDep,
    owner: BrandOwner,
    member_in: MemberCreate,
) -> MemberPublic:
    user = session.exec(select(User).where(User.email == member_in.email)).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="No user with that email. They must sign up first.",
        )
    existing = session.exec(
        select(Membership).where(
            Membership.brand_id == owner.brand_id,
            Membership.user_id == user.id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User is already a member")
    member = Membership(
        user_id=user.id,
        brand_id=owner.brand_id,
        role=member_in.role.value,
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return MemberPublic(
        id=member.id,
        user_id=member.user_id,
        email=user.email,
        full_name=user.full_name,
        role=MemberRole(member.role),
        created_at=member.created_at,
    )


@router.patch("/{brand_id}/members/{membership_id}", response_model=MemberPublic)
def update_member(
    *,
    session: SessionDep,
    owner: BrandOwner,
    membership_id: uuid.UUID,
    member_in: MemberUpdate,
) -> MemberPublic:
    member = session.get(Membership, membership_id)
    if not member or member.brand_id != owner.brand_id:
        raise HTTPException(status_code=404, detail="Membership not found")
    if member.role == MemberRole.OWNER.value and member_in.role != MemberRole.OWNER:
        _ensure_not_last_owner(session, owner.brand_id, member.id)
    member.role = member_in.role.value
    session.add(member)
    session.commit()
    session.refresh(member)
    user = session.get(User, member.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return MemberPublic(
        id=member.id,
        user_id=member.user_id,
        email=user.email,
        full_name=user.full_name,
        role=MemberRole(member.role),
        created_at=member.created_at,
    )


@router.delete("/{brand_id}/members/{membership_id}")
def delete_member(
    *, session: SessionDep, owner: BrandOwner, membership_id: uuid.UUID
) -> dict[str, str]:
    member = session.get(Membership, membership_id)
    if not member or member.brand_id != owner.brand_id:
        raise HTTPException(status_code=404, detail="Membership not found")
    if member.role == MemberRole.OWNER.value:
        _ensure_not_last_owner(session, owner.brand_id, member.id)
    session.delete(member)
    session.commit()
    return {"message": "Membership removed"}


def _ensure_not_last_owner(
    session: SessionDep, brand_id: uuid.UUID, membership_id: uuid.UUID
) -> None:
    owner_count = session.exec(
        select(func.count())
        .select_from(Membership)
        .where(
            Membership.brand_id == brand_id,
            Membership.role == MemberRole.OWNER.value,
        )
    ).one()
    is_owner = session.get(Membership, membership_id)
    if owner_count <= 1 and is_owner and is_owner.role == MemberRole.OWNER.value:
        raise HTTPException(status_code=400, detail="A brand must keep at least one owner")
