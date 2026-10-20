import uuid
from typing import Any

from sqlmodel import Session, func, select

from app.modules.brand_import.models import (
    BrandAsset,
    BrandImport,
    BrandProfile,
    ImportStatus,
    ProfileStatus,
)
from app.modules.brand_import.profile import validate_profile_json
from app.modules.brands.models import Brand
from app.providers.ai import AnalysisSource, analyze_brand
from app.providers.storage import get_storage


class ProfileAnalysisError(Exception):
    pass


def analyze_import(
    session: Session, brand: Brand, import_row: BrandImport
) -> BrandProfile:
    assets = session.exec(
        select(BrandAsset).where(
            BrandAsset.brand_id == brand.id,
            BrandAsset.import_id == import_row.id,
            BrandAsset.is_active.is_(True),  # type: ignore[attr-defined]
        )
    ).all()
    if not assets:
        raise ProfileAnalysisError("This import contains no assets to analyze")

    sources: list[AnalysisSource] = []
    for asset in assets:
        text: str | None = None
        image: bytes | None = None
        metadata: dict[str, Any] = asset.metadata_json or {}
        if isinstance(metadata.get("text_preview"), str):
            text = metadata["text_preview"]
        if asset.content_type.startswith("image/") and asset.content_type != "image/svg+xml":
            try:
                image = get_storage().read(asset.storage_key)
            except Exception:  # noqa: BLE001
                image = None
        sources.append(
            AnalysisSource(
                filename=asset.original_filename,
                asset_type=asset.asset_type,
                text=text,
                image=image,
                asset_id=str(asset.id),
            )
        )

    try:
        payload = analyze_brand(brand.name, sources)
        validated = validate_profile_json(payload)
    except Exception as exc:  # noqa: BLE001
        raise ProfileAnalysisError(
            "Brand analysis returned an invalid profile. No profile was saved."
        ) from exc

    max_version = session.exec(
        select(func.max(BrandProfile.version)).where(
            BrandProfile.brand_id == brand.id
        )
    ).one()
    profile = BrandProfile(
        brand_id=brand.id,
        version=(max_version or 0) + 1,
        status=ProfileStatus.NEEDS_REVIEW.value,
        profile_json=validated,
        created_from_import_id=import_row.id,
    )
    session.add(profile)
    import_row.status = ImportStatus.COMPLETED.value
    session.add(import_row)
    session.commit()
    session.refresh(profile)
    return profile


def latest_profile(session: Session, brand_id: uuid.UUID) -> BrandProfile | None:
    return session.exec(
        select(BrandProfile)
        .where(BrandProfile.brand_id == brand_id)
        .order_by(BrandProfile.version.desc())  # type: ignore[attr-defined]
    ).first()
