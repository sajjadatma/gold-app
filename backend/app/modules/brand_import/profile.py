import uuid
from typing import Any

from pydantic import Field
from sqlmodel import SQLModel


class Provenance(SQLModel):
    source_asset_id: uuid.UUID | None = None
    page_number: int | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)


class ColorEntry(SQLModel):
    name: str | None = None
    hex: str
    usage: str | None = None
    provenance: Provenance | None = None


class TypographyEntry(SQLModel):
    family: str
    role: str | None = None
    provenance: Provenance | None = None


class LogoEntry(SQLModel):
    asset_id: uuid.UUID | None = None
    variant: str | None = None
    provenance: Provenance | None = None


class Identity(SQLModel):
    brand_name: str = ""
    tagline: str = ""
    story: str = ""
    positioning: str = ""
    audience: list[str] = Field(default_factory=list)
    personality: list[str] = Field(default_factory=list)


class Photography(SQLModel):
    lighting: list[str] = Field(default_factory=list)
    backgrounds: list[str] = Field(default_factory=list)
    composition: list[str] = Field(default_factory=list)
    contrast: str = ""
    shadow_style: str = ""
    retouching: list[str] = Field(default_factory=list)
    prohibited_styles: list[str] = Field(default_factory=list)


class HumanModelStyle(SQLModel):
    appearance: list[str] = Field(default_factory=list)
    makeup: list[str] = Field(default_factory=list)
    hair: list[str] = Field(default_factory=list)
    wardrobe: list[str] = Field(default_factory=list)
    hands_and_nails: list[str] = Field(default_factory=list)
    posing: list[str] = Field(default_factory=list)


class ToneOfVoice(SQLModel):
    languages: list[str] = Field(default_factory=list)
    tone: list[str] = Field(default_factory=list)
    caption_style: str = ""
    emoji_policy: str = ""
    cta_style: str = ""
    hashtag_style: str = ""


class GraphicSystem(SQLModel):
    patterns: list[str] = Field(default_factory=list)
    decorative_elements: list[str] = Field(default_factory=list)
    layout_principles: list[str] = Field(default_factory=list)


class SocialMedia(SQLModel):
    preferred_ratios: list[str] = Field(default_factory=list)
    visual_rules: list[str] = Field(default_factory=list)
    logo_rules: list[str] = Field(default_factory=list)


class BrandProfileData(SQLModel):
    identity: Identity = Field(default_factory=Identity)
    colors: list[ColorEntry] = Field(default_factory=list)
    typography: list[TypographyEntry] = Field(default_factory=list)
    logos: list[LogoEntry] = Field(default_factory=list)
    photography: Photography = Field(default_factory=Photography)
    human_model_style: HumanModelStyle = Field(default_factory=HumanModelStyle)
    tone_of_voice: ToneOfVoice = Field(default_factory=ToneOfVoice)
    graphic_system: GraphicSystem = Field(default_factory=GraphicSystem)
    social_media: SocialMedia = Field(default_factory=SocialMedia)
    dos: list[str] = Field(default_factory=list)
    donts: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    provenance: list[Provenance] = Field(default_factory=list)


def validate_profile_json(payload: dict[str, Any]) -> dict[str, Any]:
    """AI output must pass this boundary before it can be persisted."""
    return BrandProfileData.model_validate(payload).model_dump(mode="json")
