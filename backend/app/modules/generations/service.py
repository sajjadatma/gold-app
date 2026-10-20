import io
import uuid
from datetime import UTC, datetime
from typing import Any

from PIL import Image
from sqlmodel import Session, select

from app.core.config import settings
from app.modules.brand_import.models import BrandProfile
from app.modules.brand_models.models import BrandModel, BrandModelReference
from app.modules.generations.models import (
    GeneratedAsset,
    GenerationMode,
    GenerationRequest,
    GenerationStatus,
    IntegrityStatus,
)
from app.modules.products.models import Product, ProductImage
from app.providers.ai import generate_image
from app.providers.storage import build_storage_key, get_storage


class GenerationError(Exception):
    pass


def build_prompt(
    mode: str,
    profile_json: dict[str, Any],
    product: Product,
    model: BrandModel | None,
    style_notes: str,
) -> str:
    identity = profile_json.get("identity", {})
    photography = profile_json.get("photography", {})
    graphic = profile_json.get("graphic_system", {})
    camera = (
        f"Photography rules: lighting={photography.get('lighting', [])}, "
        f"backgrounds={photography.get('backgrounds', [])}, "
        f"composition={photography.get('composition', [])}, "
        f"contrast={photography.get('contrast', '')}, "
        f"avoid={photography.get('prohibited_styles', [])}."
    )
    product_text = (
        f"Product: {product.name}. Category: {product.category}. "
        f"Metal: {product.metal_type or 'unknown'} / {product.metal_color or 'unknown'}. "
        f"Stone: {product.stone_type or 'unknown'}. "
        f"Notes: {product.integrity_notes or 'none'}."
    )
    fidelity = (
        "Preserve the jewelry exactly: silhouette, major geometry, visible stone count, "
        "stone placement, band/chain/pendant structure, metal color, and decorative elements. "
        "Do not add or remove major elements. No text, no watermark, no extra jewelry."
    )
    mode_text = {
        GenerationMode.STUDIO.value: (
            "Create a high-end studio product photograph of this exact jewelry piece."
        ),
        GenerationMode.ON_MODEL.value: (
            "Place this exact jewelry piece on the provided brand model. "
            "Keep the model's canonical appearance consistent."
        ),
        GenerationMode.CAMPAIGN.value: (
            "Create a branded campaign advertising image featuring this exact jewelry piece. "
            f"Use the brand graphic system: {graphic}."
        ),
    }.get(mode, "Create a professional jewelry image.")
    model_text = ""
    if model:
        model_text = f"Model direction: {model.name} — {model.config_json}."
    return (
        f"Brand: {identity.get('brand_name', '')}. Tagline: {identity.get('tagline', '')}. "
        f"Positioning: {identity.get('positioning', '')}. Colors: {profile_json.get('colors', [])}. "
        f"{camera} {product_text} {mode_text} {model_text} "
        f"Additional direction: {style_notes or 'none'}. {fidelity}"
    )


def _pick_source_image(
    session: Session, product_id: uuid.UUID, image_id: uuid.UUID | None
) -> ProductImage:
    images = session.exec(
        select(ProductImage).where(ProductImage.product_id == product_id)
    ).all()
    if not images:
        raise GenerationError("Product has no source image")
    if image_id:
        chosen = next((image for image in images if image.id == image_id), None)
        if not chosen:
            raise GenerationError("Selected source image does not belong to the product")
        return chosen
    primary = next((image for image in images if image.is_primary), None)
    return primary or images[0]


def run_generation(session: Session, request_id: uuid.UUID) -> GenerationRequest:
    request = session.get(GenerationRequest, request_id)
    if not request:
        raise GenerationError("Generation request not found")
    product = session.get(Product, request.product_id)
    profile = session.get(BrandProfile, request.brand_profile_id)
    if not product or not profile:
        raise GenerationError("Generation inputs are missing")
    model = session.get(BrandModel, request.brand_model_id) if request.brand_model_id else None

    request.status = GenerationStatus.PROCESSING.value
    request.error_message = None
    request.updated_at = datetime.now(UTC)
    session.add(request)
    session.commit()

    try:
        parameters = request.parameters_json or {}
        source_image = _pick_source_image(
            session,
            product.id,
            uuid.UUID(parameters["source_image_id"])
            if parameters.get("source_image_id")
            else None,
        )
        source_bytes = get_storage().read(source_image.storage_key)
        sources = [source_bytes]
        if model:
            references = session.exec(
                select(BrandModelReference).where(
                    BrandModelReference.brand_model_id == model.id,
                    BrandModelReference.is_canonical.is_(True),  # type: ignore[attr-defined]
                )
            ).all()
            if references:
                sources.append(get_storage().read(references[0].storage_key))

        prompt = build_prompt(
            request.mode,
            profile.profile_json,
            product,
            model,
            str(parameters.get("style_notes", "")),
        )
        image_bytes = generate_image(prompt, sources, request.aspect_ratio)
        with Image.open(io.BytesIO(image_bytes)) as image:
            width, height = image.size
        key = build_storage_key(
            request.brand_id, f"generations/{request.id}", "result.png"
        )
        get_storage().save(key, image_bytes, "image/png")
        asset = GeneratedAsset(
            generation_request_id=request.id,
            storage_key=key,
            content_type="image/png",
            width=width,
            height=height,
            integrity_status=IntegrityStatus.PENDING.value,
        )
        session.add(asset)
        request.status = GenerationStatus.COMPLETED.value
        request.provider = settings.AI_PROVIDER
        request.model = settings.AI_IMAGE_MODEL
        request.parameters_json = {**parameters, "prompt": prompt[:4000]}
        request.updated_at = datetime.now(UTC)
        session.add(request)
        session.commit()
        session.refresh(request)
        return request
    except Exception as exc:  # noqa: BLE001
        request.status = GenerationStatus.FAILED.value
        request.error_message = "Image generation failed. Please retry."
        request.updated_at = datetime.now(UTC)
        session.add(request)
        session.commit()
        raise GenerationError(request.error_message) from exc
