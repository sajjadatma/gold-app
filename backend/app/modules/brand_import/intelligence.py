import uuid
from typing import Any

from sqlmodel import Session, func, select

from app.core.config import settings
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
from app.providers.ocr import OcrError, extract_pdf_text, ocr_available
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
    ocr_issues: list[str] = []
    session_id = f"brand-{brand.id}-import-{import_row.id}"
    for asset in assets:
        text: str | None = None
        image: bytes | None = None
        metadata: dict[str, Any] = dict(asset.metadata_json or {})
        for key in ("text", "text_preview"):
            if isinstance(metadata.get(key), str) and metadata[key].strip():
                text = metadata[key]
                break

        if (
            asset.content_type == "application/pdf"
            and ocr_available()
            and (not text or len(text.strip()) < settings.OCR_MIN_TEXT_CHARS)
        ):
            try:
                pdf_bytes = get_storage().read(asset.storage_key)
                ocr_text = extract_pdf_text(
                    pdf_bytes, asset.original_filename, session_id
                )
                metadata["text"] = ocr_text
                metadata["ocr"] = {
                    "model": settings.OCR_MODEL,
                    "provider": settings.OCR_API_BASE,
                }
                asset.metadata_json = metadata
                asset.page_count = asset.page_count or ocr_text.count("[Page ")
                session.add(asset)
                text = ocr_text
            except OcrError:
                ocr_issues.append(
                    f"OCR could not read {asset.original_filename}; confirm its brand rules manually."
                )
            except Exception:  # noqa: BLE001
                ocr_issues.append(
                    f"OCR could not read {asset.original_filename}; confirm its brand rules manually."
                )

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
        if ocr_issues:
            validated["uncertainties"] = [
                *validated.get("uncertainties", []),
                *ocr_issues,
            ]
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
