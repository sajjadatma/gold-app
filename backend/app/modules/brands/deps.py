import uuid
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep
from app.modules.brands.models import Brand, MemberRole, Membership


def get_brand_membership(
    brand_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Membership:
    brand = session.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    membership = session.exec(
        select(Membership).where(
            Membership.brand_id == brand_id,
            Membership.user_id == current_user.id,
        )
    ).first()
    if not membership:
        # Do not reveal that the brand exists to unrelated users.
        raise HTTPException(status_code=404, detail="Brand not found")
    return membership


BrandMembership = Annotated[Membership, Depends(get_brand_membership)]


def get_brand_owner(membership: BrandMembership) -> Membership:
    if membership.role != MemberRole.OWNER.value:
        raise HTTPException(status_code=403, detail="Owner role required")
    return membership


BrandOwner = Annotated[Membership, Depends(get_brand_owner)]


def require_membership(session: Session, user_id: uuid.UUID, brand_id: uuid.UUID) -> None:
    """Guard child resources that are reached without the brand path dependency."""
    membership = session.exec(
        select(Membership).where(
            Membership.brand_id == brand_id,
            Membership.user_id == user_id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Brand not found")
