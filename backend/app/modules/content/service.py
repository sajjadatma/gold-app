import uuid

from sqlmodel import Session

from app.modules.brand_import.models import BrandProfile
from app.modules.brand_models.models import BrandModel
from app.modules.content.models import ContentDraft
from app.modules.content.schemas import CaptionResult
from app.modules.generations.models import GeneratedAsset, GenerationRequest
from app.modules.products.models import Product
from app.providers.ai import generate_caption


class CaptionGenerationError(Exception):
    pass


def generate_caption_for_draft(
    session: Session, draft: ContentDraft, force: bool = False
) -> ContentDraft:
    if draft.user_edited and not force:
        raise CaptionGenerationError(
            "Caption was edited manually. Regenerate only with explicit confirmation."
        )
    asset = session.get(GeneratedAsset, draft.generated_asset_id)
    if not asset:
        raise CaptionGenerationError("Generated asset not found")
    request = session.get(GenerationRequest, asset.generation_request_id)
    if not request:
        raise CaptionGenerationError("Generation request not found")
    product = session.get(Product, draft.product_id)
    profile = session.get(BrandProfile, request.brand_profile_id)
    if not product or not profile:
        raise CaptionGenerationError("Caption inputs are missing")
    brand_name = str(profile.profile_json.get("identity", {}).get("brand_name", ""))
    try:
        payload = generate_caption(
            brand_name,
            profile.profile_json,
            product.name,
            product.category,
            product.metal_color,
            product.stone_type,
        )
        result = CaptionResult.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        raise CaptionGenerationError(
            "Caption generation returned an invalid response. Nothing was overwritten."
        ) from exc

    draft.caption = result.primary_caption
    draft.alternative_captions_json = result.alternatives
    draft.cta = result.cta
    draft.hashtags = " ".join(tag for tag in result.hashtags if tag.strip())
    draft.user_edited = False
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return draft


def draft_detail_fields(
    session: Session, draft: ContentDraft
) -> tuple[GeneratedAsset, GenerationRequest, Product, BrandProfile, BrandModel | None]:
    asset = session.get(GeneratedAsset, draft.generated_asset_id)
    if not asset:
        raise CaptionGenerationError("Generated asset not found")
    request = session.get(GenerationRequest, asset.generation_request_id)
    if not request:
        raise CaptionGenerationError("Generation request not found")
    product = session.get(Product, draft.product_id)
    profile = session.get(BrandProfile, request.brand_profile_id)
    model = (
        session.get(BrandModel, request.brand_model_id)
        if request.brand_model_id
        else None
    )
    if not product or not profile:
        raise CaptionGenerationError("Draft references are missing")
    return asset, request, product, profile, model


def asset_belongs_to_brand(
    session: Session, asset_id: uuid.UUID, brand_id: uuid.UUID
) -> tuple[GeneratedAsset, GenerationRequest]:
    asset = session.get(GeneratedAsset, asset_id)
    if not asset:
        raise CaptionGenerationError("Generated asset not found")
    request = session.get(GenerationRequest, asset.generation_request_id)
    if not request or request.brand_id != brand_id:
        raise CaptionGenerationError("Generated asset not found")
    return asset, request
