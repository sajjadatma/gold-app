import base64
import io
import json
import re
from dataclasses import dataclass
from typing import Any, cast

import httpx
from PIL import Image

from app.core.config import settings


@dataclass
class AnalysisSource:
    filename: str
    asset_type: str
    text: str | None = None
    image: bytes | None = None
    asset_id: str | None = None


def _dominant_colors(image_bytes: bytes) -> list[str]:
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image.thumbnail((64, 64))
        quantized = image.quantize(colors=5)
        palette = quantized.getpalette() or []
        counts = sorted(quantized.getcolors() or [], reverse=True)
        colors: list[str] = []
        for _count, index in counts[:3]:
            color_index = cast(int, index) * 3
            red, green, blue = palette[color_index : color_index + 3]
            colors.append(f"#{red:02X}{green:02X}{blue:02X}")
        return colors
    except Exception:  # noqa: BLE001
        return []


def _fake_analysis(brand_name: str, sources: list[AnalysisSource]) -> dict[str, Any]:
    colors: list[dict[str, Any]] = []
    typography: list[dict[str, Any]] = []
    logos: list[dict[str, Any]] = []
    uncertainties: list[str] = []
    provenance: list[dict[str, Any]] = []

    for source in sources:
        if source.image:
            for hex_value in _dominant_colors(source.image):
                if any(item["hex"] == hex_value for item in colors):
                    continue
                colors.append(
                    {
                        "name": None,
                        "hex": hex_value,
                        "usage": None,
                        "provenance": {
                            "source_asset_id": source.asset_id,
                            "page_number": None,
                            "confidence": 0.6,
                        },
                    }
                )
        if source.asset_type == "font":
            family = re.sub(r"\.[A-Za-z0-9]+$", "", source.filename).replace("_", " ")
            typography.append(
                {
                    "family": family,
                    "role": None,
                    "provenance": {
                        "source_asset_id": source.asset_id,
                        "page_number": None,
                        "confidence": 0.9,
                    },
                }
            )
        if source.asset_type == "logo" or "logo" in source.filename.lower():
            if source.asset_id and not any(
                item["asset_id"] == source.asset_id for item in logos
            ):
                logos.append(
                    {
                        "asset_id": source.asset_id,
                        "variant": None,
                        "provenance": {
                            "source_asset_id": source.asset_id,
                            "page_number": None,
                            "confidence": 0.8,
                        },
                    }
                )
        if source.asset_id:
            provenance.append(
                {
                    "source_asset_id": source.asset_id,
                    "page_number": None,
                    "confidence": 0.5,
                }
            )

    if not colors:
        uncertainties.append("No colors could be extracted from the imported assets.")
    if not typography:
        uncertainties.append("No font files were found in the import.")
    if not logos:
        uncertainties.append("No logo asset was identified with confidence.")
    uncertainties.append(
        "Identity narrative, audience, photography rules, and tone of voice must be confirmed by the Owner; the fake provider does not invent them."
    )

    return {
        "identity": {
            "brand_name": brand_name,
            "tagline": "",
            "story": "",
            "positioning": "",
            "audience": [],
            "personality": [],
        },
        "colors": colors,
        "typography": typography,
        "logos": logos,
        "photography": {
            "lighting": [],
            "backgrounds": [],
            "composition": [],
            "contrast": "",
            "shadow_style": "",
            "retouching": [],
            "prohibited_styles": [],
        },
        "human_model_style": {
            "appearance": [],
            "makeup": [],
            "hair": [],
            "wardrobe": [],
            "hands_and_nails": [],
            "posing": [],
        },
        "tone_of_voice": {
            "languages": [],
            "tone": [],
            "caption_style": "",
            "emoji_policy": "",
            "cta_style": "",
            "hashtag_style": "",
        },
        "graphic_system": {
            "patterns": [],
            "decorative_elements": [],
            "layout_principles": [],
        },
        "social_media": {
            "preferred_ratios": [],
            "visual_rules": [],
            "logo_rules": [],
        },
        "dos": [],
        "donts": [],
        "uncertainties": uncertainties,
        "provenance": provenance,
    }


def _real_analysis(brand_name: str, sources: list[AnalysisSource]) -> dict[str, Any]:
    text_blocks = [
        f"File: {source.filename} ({source.asset_type})\n{source.text or ''}"
        for source in sources
        if source.text
    ]
    image_sources = [source for source in sources if source.image][:4]
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "Analyze the existing brand identity of this jewelry brand. "
                "Return ONLY JSON with keys: identity{brand_name,tagline,story,positioning,audience,personality}, "
                "colors[{name,hex,usage}], typography[{family,role}], logos[], "
                "photography{lighting,backgrounds,composition,contrast,shadow_style,retouching,prohibited_styles}, "
                "human_model_style{appearance,makeup,hair,wardrobe,hands_and_nails,posing}, "
                "tone_of_voice{languages,tone,caption_style,emoji_policy,cta_style,hashtag_style}, "
                "graphic_system{patterns,decorative_elements,layout_principles}, "
                "social_media{preferred_ratios,visual_rules,logo_rules}, dos, donts, uncertainties. "
                "Do not invent missing rules; use empty values and list them in uncertainties. "
                f"Brand name: {brand_name}.\n\n" + "\n\n".join(text_blocks)[:24000]
            ),
        }
    ]
    for source in image_sources:
        encoded = base64.b64encode(source.image or b"").decode()
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{encoded}"},
            }
        )

    response = httpx.post(
        f"{settings.AI_API_BASE.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
        json={
            "model": settings.AI_VISION_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You extract existing brand identity. Output valid JSON only.",
                },
                {"role": "user", "content": content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        },
        timeout=120,
    )
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"]
    if raw.strip().startswith("```"):
        raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("AI response was not a JSON object")
    return parsed


def analyze_brand(brand_name: str, sources: list[AnalysisSource]) -> dict[str, Any]:
    if settings.AI_PROVIDER == "openai" and settings.AI_API_KEY:
        return _real_analysis(brand_name, sources)
    return _fake_analysis(brand_name, sources)
