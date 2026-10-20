import base64
import io
import json
import re
from dataclasses import dataclass
from typing import Any, cast

import httpx
from PIL import Image, ImageDraw

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


ASPECT_SIZES: dict[str, tuple[int, int]] = {
    "1:1": (1024, 1024),
    "4:5": (1024, 1280),
    "9:16": (1024, 1792),
    "16:9": (1792, 1024),
}


def _fake_canvas(width: int, height: int) -> Image.Image:
    canvas = Image.new("RGB", (width, height), (238, 232, 220))
    draw = ImageDraw.Draw(canvas)
    for y in range(height):
        shade = 238 - int(24 * y / max(height - 1, 1))
        draw.line([(0, y), (width, y)], fill=(shade, shade - 4, shade - 12))
    return canvas


def _fake_image(prompt: str, sources: list[bytes], aspect_ratio: str) -> bytes:
    width, height = ASPECT_SIZES.get(aspect_ratio, (1024, 1024))
    canvas = _fake_canvas(width, height)
    if sources:
        try:
            source = Image.open(io.BytesIO(sources[0])).convert("RGBA")
            source.thumbnail((int(width * 0.62), int(height * 0.62)))
            x = (width - source.width) // 2
            y = (height - source.height) // 2 - int(height * 0.04)
            canvas.paste(source, (x, y), source)
        except Exception:  # noqa: BLE001
            pass
    draw = ImageDraw.Draw(canvas)
    label = "Fake provider preview"
    draw.rectangle([0, height - 48, width, height], fill=(24, 22, 20))
    draw.text((24, height - 36), label, fill=(230, 220, 200))
    draw.text((24, 24), prompt[:60], fill=(70, 62, 52))
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    return buffer.getvalue()


def _real_image(prompt: str, sources: list[bytes], aspect_ratio: str) -> bytes:
    width, height = ASPECT_SIZES.get(aspect_ratio, (1024, 1024))
    size = f"{width}x{height}"
    headers = {"Authorization": f"Bearer {settings.AI_API_KEY}"}
    base = settings.AI_API_BASE.rstrip("/")
    if sources:
        files = {"image": ("source.png", sources[0], "image/png")}
        data = {
            "model": settings.AI_IMAGE_MODEL,
            "prompt": prompt,
            "size": size,
            "n": "1",
        }
        response = httpx.post(
            f"{base}/images/edits", headers=headers, data=data, files=files, timeout=180
        )
    else:
        response = httpx.post(
            f"{base}/images/generations",
            headers=headers,
            json={"model": settings.AI_IMAGE_MODEL, "prompt": prompt, "size": size, "n": 1},
            timeout=180,
        )
    response.raise_for_status()
    item = response.json()["data"][0]
    if item.get("b64_json"):
        from base64 import b64decode

        return b64decode(item["b64_json"])
    image_response = httpx.get(item["url"], timeout=120)
    image_response.raise_for_status()
    return image_response.content


def generate_image(prompt: str, sources: list[bytes], aspect_ratio: str) -> bytes:
    if settings.AI_PROVIDER == "openai" and settings.AI_API_KEY:
        return _real_image(prompt, sources, aspect_ratio)
    return _fake_image(prompt, sources, aspect_ratio)


def generate_model_previews(
    brand_name: str, config: dict[str, Any], count: int = 3
) -> list[bytes]:
    prompt = (
        f"Professional jewelry brand model reference for {brand_name}. "
        f"Direction: {json.dumps(config, ensure_ascii=True)[:1200]}"
    )
    return [generate_image(prompt, [], "4:5") for _ in range(count)]


def generate_text(system: str, prompt: str) -> str:
    if settings.AI_PROVIDER == "openai" and settings.AI_API_KEY:
        response = httpx.post(
            f"{settings.AI_API_BASE.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
            json={
                "model": settings.AI_TEXT_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
            },
            timeout=90,
        )
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"]).strip()
    return "Fake provider response"


def _image_difference(source: bytes, generated: bytes) -> float:
    try:
        first = Image.open(io.BytesIO(source)).convert("L").resize((64, 64))
        second = Image.open(io.BytesIO(generated)).convert("L").resize((64, 64))
        first_pixels = list(first.getdata())
        second_pixels = list(second.getdata())
        return sum(
            abs(int(a) - int(b)) for a, b in zip(first_pixels, second_pixels, strict=True)
        ) / len(first_pixels)
    except Exception:  # noqa: BLE001
        return 255.0


def evaluate_integrity(
    source: bytes, generated: bytes, product_name: str, notes: str = ""
) -> dict[str, Any]:
    if settings.AI_PROVIDER == "openai" and settings.AI_API_KEY:
        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    "Compare the source jewelry photo with the generated image. "
                    f"Product: {product_name}. Known notes: {notes or 'none'}. "
                    "Return JSON: {status: passed|needs_review|failed, summary: string, "
                    "checks: [{name, result, note}], confidence: 0-1}. "
                    "Check silhouette, major geometry, visible stone count, stone placement, "
                    "ring/band/chain structure, pendant geometry, metal color, missing or added elements. "
                    "Be conservative; do not claim certainty."
                ),
            }
        ]
        for label, data in (("source", source), ("generated", generated)):
            content.append(
                {
                    "type": "text",
                    "text": f"{label} image:",
                }
            )
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,"
                        + base64.b64encode(data).decode()
                    },
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
                        "content": "You verify jewelry product fidelity. Output valid JSON only.",
                    },
                    {"role": "user", "content": content},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
            },
            timeout=120,
        )
        response.raise_for_status()
        parsed = json.loads(response.json()["choices"][0]["message"]["content"])
        if not isinstance(parsed, dict):
            raise ValueError("Integrity response was not an object")
        return parsed

    difference = _image_difference(source, generated)
    if difference < 45:
        status = "passed"
        summary = "Source and generated jewelry are visually consistent (fake provider)."
    elif difference < 70:
        status = "needs_review"
        summary = "Some visual differences were detected; compare source and output (fake provider)."
    else:
        status = "failed"
        summary = "The generated image differs materially from the source (fake provider)."
    checks = [
        {
            "name": "overall_similarity",
            "result": status,
            "note": f"Mean grayscale difference: {difference:.1f}",
        },
        {
            "name": "human_confirmation",
            "result": "required",
            "note": "Automatic evaluation is approximate; Owner approval is mandatory.",
        },
    ]
    return {
        "status": status,
        "summary": summary,
        "checks": checks,
        "confidence": 0.55,
    }
