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


HEADING_ALIASES: dict[str, str] = {
    "brand name": "brand_name",
    "name": "brand_name",
    "tagline": "tagline",
    "slogan": "tagline",
    "brand story": "story",
    "our story": "story",
    "story": "story",
    "about us": "story",
    "about": "story",
    "brand background": "story",
    "positioning": "positioning",
    "brand positioning": "positioning",
    "position": "positioning",
    "target audience": "audience",
    "audience": "audience",
    "customer": "audience",
    "customers": "audience",
    "who we serve": "audience",
    "brand personality": "personality",
    "personality": "personality",
    "traits": "personality",
    "tone of voice": "tone",
    "verbal identity": "tone",
    "voice": "tone",
    "tone": "tone",
    "photography": "photography",
    "photography style": "photography",
    "art direction": "photography",
    "imagery": "photography",
    "visual style": "photography",
    "lighting": "lighting",
    "backgrounds": "backgrounds",
    "composition": "composition",
    "human model": "human",
    "human models": "human",
    "model direction": "human",
    "casting": "human",
    "makeup": "makeup",
    "hair": "hair",
    "wardrobe": "wardrobe",
    "nails": "nails",
    "graphic system": "graphic",
    "graphic elements": "graphic",
    "patterns": "patterns",
    "decorative elements": "decorative",
    "layout": "layout",
    "layout principles": "layout",
    "social media": "social",
    "instagram": "social",
    "preferred ratios": "ratios",
    "visual rules": "visual_rules",
    "logo rules": "logo_rules",
    "colors": "colors",
    "colour": "colors",
    "colors palette": "colors",
    "color palette": "colors",
    "colour palette": "colors",
    "palette": "colors",
    "typography": "typography",
    "typeface": "typography",
    "typefaces": "typography",
    "fonts": "typography",
    "font": "typography",
    "dos": "dos",
    "do": "dos",
    "do's": "dos",
    "donts": "donts",
    "don'ts": "donts",
    "don't": "donts",
    "avoid": "donts",
}

PAGE_MARKER = re.compile(r"^\[Page (\d+)\]$")
HEX_COLOR = re.compile(r"#([0-9A-Fa-f]{6})\b")
LABEL_LINE = re.compile(r"^([A-Za-z][A-Za-z &/'()\-]{1,40}):\s*(.+)$")


def _empty_profile(brand_name: str) -> dict[str, Any]:
    return {
        "identity": {
            "brand_name": brand_name,
            "tagline": "",
            "story": "",
            "positioning": "",
            "audience": [],
            "personality": [],
        },
        "colors": [],
        "typography": [],
        "logos": [],
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
        "additional_sections": [],
        "dos": [],
        "donts": [],
        "uncertainties": [],
        "provenance": [],
    }


def _heading_key(line: str) -> str | None:
    cleaned = re.sub(r"^[0-9]+[.)\-\s]+", "", line.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip().strip(":").lower()
    return HEADING_ALIASES.get(cleaned)


def _collect_text_blocks(text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    page: int | None = None
    previous_blank = True
    for raw_line in text.splitlines():
        line = raw_line.strip()
        marker = PAGE_MARKER.match(line)
        if marker:
            page = int(marker.group(1))
            previous_blank = True
            continue
        if not line:
            previous_blank = True
            continue
        key = _heading_key(line)
        is_heading = key is not None
        numbered_heading = bool(re.match(r"^[0-9]+[.)\-\s]+", line))
        if not is_heading:
            words = line.split()
            # Brand-book section titles are commonly all-caps, with or without
            # surrounding blank lines (PDF extraction often drops them).
            is_heading = (
                (previous_blank or numbered_heading or line.isupper())
                and len(line) <= 60
                and not re.search(r"[.!?;:]$", line)
                and len(words) <= 8
                and line.isupper()
            )
        if is_heading:
            if current and current["lines"]:
                blocks.append(current)
            current = {
                "title": line.strip().strip(":"),
                "key": key,
                "page": page,
                "lines": [],
            }
        elif current is not None:
            current["lines"].append(line)
        previous_blank = False
    if current and current["lines"]:
        blocks.append(current)
    return blocks


def _split_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    for line in lines:
        cleaned = re.sub(r"^[\-\u2022*\u00b7]\s*", "", line).strip()
        if not cleaned:
            continue
        if len(cleaned) <= 160:
            parts = re.split(r"[,;\u2022]", cleaned)
        else:
            parts = [cleaned]
        for part in parts:
            value = part.strip(" .")
            if value:
                items.append(value)
    return items


def _labeled(lines: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in lines:
        match = LABEL_LINE.match(line)
        if match:
            values[match.group(1).strip().lower()] = match.group(2).strip()
    return values


def _text_content(lines: list[str], limit: int = 4000) -> str:
    return " ".join(line.strip() for line in lines if line.strip())[:limit]


def _add_unique(target: list[Any], value: Any) -> None:
    if value not in target:
        target.append(value)


def _extract_colors_from_text(
    text: str, page: int | None, asset_id: str | None
) -> list[dict[str, Any]]:
    colors: list[dict[str, Any]] = []
    for line in text.splitlines():
        for hex_value in HEX_COLOR.findall(line):
            name: str | None = None
            prefix = re.split(r"#", line, maxsplit=1)[0].strip(" :-")
            if prefix and len(prefix) <= 40:
                name = prefix
            colors.append(
                {
                    "name": name,
                    "hex": f"#{hex_value.upper()}",
                    "usage": None,
                    "provenance": {
                        "source_asset_id": asset_id,
                        "page_number": page,
                        "confidence": 0.8,
                    },
                }
            )
    return colors


def _extract_fonts_from_text(
    lines: list[str], page: int | None, asset_id: str | None
) -> list[dict[str, Any]]:
    fonts: list[dict[str, Any]] = []
    for line in lines:
        cleaned = re.sub(r"^[\-\u2022*]\s*", "", line).strip()
        if not cleaned:
            continue
        role: str | None = None
        family = cleaned
        match = LABEL_LINE.match(cleaned)
        if match:
            role = match.group(1).strip()
            family = match.group(2).strip()
        else:
            for separator in ("\u2014", " - "):
                if separator in cleaned:
                    role, family = cleaned.split(separator, 1)
                    break
        family = family.strip(" .")
        if not family or len(family) > 80:
            continue
        fonts.append(
            {
                "family": family,
                "role": role.strip() if role else None,
                "provenance": {
                    "source_asset_id": asset_id,
                    "page_number": page,
                    "confidence": 0.7,
                },
            }
        )
    return fonts


def _apply_tone_block(profile: dict[str, Any], lines: list[str]) -> None:
    values = _labeled(lines)
    tone = profile["tone_of_voice"]
    for key, target in (
        ("languages", "languages"),
        ("language", "languages"),
        ("tone", "tone"),
        ("caption", "caption_style"),
        ("caption style", "caption_style"),
        ("emoji", "emoji_policy"),
        ("emoji policy", "emoji_policy"),
        ("cta", "cta_style"),
        ("cta style", "cta_style"),
        ("hashtag", "hashtag_style"),
        ("hashtags", "hashtag_style"),
        ("hashtag style", "hashtag_style"),
    ):
        if key not in values:
            continue
        if target in {"languages", "tone"}:
            for item in _split_items([values[key]]):
                _add_unique(tone[target], item)
        else:
            tone[target] = values[key]
    unlabeled = [line for line in lines if not LABEL_LINE.match(line)]
    if unlabeled and not values:
        for item in _split_items(unlabeled):
            _add_unique(tone["tone"], item)


def _apply_text_source(profile: dict[str, Any], text: str, asset_id: str | None) -> None:
    blocks = _collect_text_blocks(text)
    for block in blocks:
        key = block["key"]
        lines: list[str] = block["lines"]
        page: int | None = block["page"]
        content = _text_content(lines)
        values = _labeled(lines)
        if key == "brand_name" and content:
            profile["identity"]["brand_name"] = content[:255]
        elif key == "tagline" and content:
            profile["identity"]["tagline"] = content[:500]
        elif key == "story" and content:
            profile["identity"]["story"] = content[:4000]
        elif key == "positioning" and content:
            profile["identity"]["positioning"] = content[:2000]
        elif key == "audience":
            for item in _split_items(lines):
                _add_unique(profile["identity"]["audience"], item)
        elif key == "personality":
            for item in _split_items(lines):
                _add_unique(profile["identity"]["personality"], item)
        elif key == "tone":
            _apply_tone_block(profile, lines)
        elif key in {"photography", "lighting", "backgrounds", "composition"}:
            photography = profile["photography"]
            sub = {
                "lighting": "lighting",
                "backgrounds": "backgrounds",
                "composition": "composition",
                "contrast": "contrast",
                "shadow": "shadow_style",
                "shadow style": "shadow_style",
                "retouching": "retouching",
                "avoid": "prohibited_styles",
                "prohibited": "prohibited_styles",
            }
            for label, item in values.items():
                target = sub.get(label)
                if not target:
                    continue
                if target in {"contrast", "shadow_style"}:
                    photography[target] = item
                else:
                    for entry in _split_items([item]):
                        _add_unique(photography[target], entry)
            if key in {"lighting", "backgrounds", "composition"}:
                for item in _split_items(lines):
                    _add_unique(photography[key], item)
            else:
                for item in _split_items(
                    [line for line in lines if not LABEL_LINE.match(line)]
                ):
                    _add_unique(photography["composition"], item)
            photography["prohibited_styles"] = _split_items(
                values.get("prohibited styles", "").split(",")
            ) or photography["prohibited_styles"]
        elif key in {
            "human",
            "makeup",
            "hair",
            "wardrobe",
            "nails",
        }:
            human = profile["human_model_style"]
            sub = {
                "appearance": "appearance",
                "look": "appearance",
                "makeup": "makeup",
                "hair": "hair",
                "wardrobe": "wardrobe",
                "styling": "wardrobe",
                "hands": "hands_and_nails",
                "nails": "hands_and_nails",
                "hands and nails": "hands_and_nails",
                "posing": "posing",
                "pose": "posing",
            }
            for label, item in values.items():
                target = sub.get(label)
                if target:
                    for entry in _split_items([item]):
                        _add_unique(human[target], entry)
            direct = {
                "makeup": "makeup",
                "hair": "hair",
                "wardrobe": "wardrobe",
                "nails": "hands_and_nails",
            }.get(key or "")
            if direct:
                for item in _split_items(lines):
                    _add_unique(human[direct], item)
            elif key == "human":
                for item in _split_items(
                    [line for line in lines if not LABEL_LINE.match(line)]
                ):
                    _add_unique(human["appearance"], item)
        elif key in {"graphic", "patterns", "decorative", "layout"}:
            graphic = profile["graphic_system"]
            sub = {
                "patterns": "patterns",
                "pattern": "patterns",
                "decorative": "decorative_elements",
                "decorative elements": "decorative_elements",
                "layout": "layout_principles",
                "layout principles": "layout_principles",
            }
            for label, item in values.items():
                target = sub.get(label)
                if target:
                    for entry in _split_items([item]):
                        _add_unique(graphic[target], entry)
            direct = {"patterns": "patterns", "decorative": "decorative_elements", "layout": "layout_principles"}.get(key or "")
            if direct:
                for item in _split_items(lines):
                    _add_unique(graphic[direct], item)
            elif key == "graphic":
                for item in _split_items(
                    [line for line in lines if not LABEL_LINE.match(line)]
                ):
                    _add_unique(graphic["patterns"], item)
        elif key in {"social", "ratios", "visual_rules", "logo_rules"}:
            social = profile["social_media"]
            sub = {
                "ratios": "preferred_ratios",
                "preferred ratios": "preferred_ratios",
                "visual rules": "visual_rules",
                "rules": "visual_rules",
                "logo": "logo_rules",
                "logo rules": "logo_rules",
            }
            for label, item in values.items():
                target = sub.get(label)
                if target:
                    for entry in _split_items([item]):
                        _add_unique(social[target], entry)
            direct = {"ratios": "preferred_ratios", "visual_rules": "visual_rules", "logo_rules": "logo_rules"}.get(key or "")
            if direct:
                for item in _split_items(lines):
                    _add_unique(social[direct], item)
            elif key == "social":
                for item in _split_items(
                    [line for line in lines if not LABEL_LINE.match(line)]
                ):
                    _add_unique(social["visual_rules"], item)
        elif key == "colors":
            for color in _extract_colors_from_text("\n".join(lines), page, asset_id):
                if not any(item["hex"] == color["hex"] for item in profile["colors"]):
                    profile["colors"].append(color)
            if values:
                for label, value in values.items():
                    if HEX_COLOR.search(value):
                        for color in _extract_colors_from_text(
                            f"{label}: {value}", page, asset_id
                        ):
                            color["name"] = label.title()
                            if not any(
                                item["hex"] == color["hex"] for item in profile["colors"]
                            ):
                                profile["colors"].append(color)
        elif key == "typography":
            for font in _extract_fonts_from_text(lines, page, asset_id):
                if not any(
                    item["family"].lower() == font["family"].lower()
                    for item in profile["typography"]
                ):
                    profile["typography"].append(font)
        elif key == "dos":
            for item in _split_items(lines):
                _add_unique(profile["dos"], item)
        elif key == "donts":
            for item in _split_items(lines):
                _add_unique(profile["donts"], item)
        elif block["title"]:
            clean_title = re.sub(
                r"^[0-9]+[.)\-\s]+", "", block["title"]
            ).strip()
            profile["additional_sections"].append(
                {
                    "title": clean_title[:255],
                    "content": lines[:40],
                    "page_number": page,
                    "confidence": 0.6,
                }
            )

    for color in _extract_colors_from_text(text, None, asset_id):
        if not any(item["hex"] == color["hex"] for item in profile["colors"]):
            profile["colors"].append(color)
    if asset_id:
        profile["provenance"].append(
            {
                "source_asset_id": asset_id,
                "page_number": None,
                "confidence": 0.6,
            }
        )


def _fake_analysis(brand_name: str, sources: list[AnalysisSource]) -> dict[str, Any]:
    profile = _empty_profile(brand_name)
    uncertainties: list[str] = []
    text_found = False

    for source in sources:
        if source.image:
            for hex_value in _dominant_colors(source.image):
                if any(item["hex"] == hex_value for item in profile["colors"]):
                    continue
                profile["colors"].append(
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
            if not any(
                item["family"].lower() == family.lower()
                for item in profile["typography"]
            ):
                profile["typography"].append(
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
                item["asset_id"] == source.asset_id for item in profile["logos"]
            ):
                profile["logos"].append(
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
        if source.text:
            text_found = True
            _apply_text_source(profile, source.text, source.asset_id)
        if source.asset_id:
            profile["provenance"].append(
                {
                    "source_asset_id": source.asset_id,
                    "page_number": None,
                    "confidence": 0.5,
                }
            )

    identity = profile["identity"]
    if not profile["colors"]:
        uncertainties.append("No colors could be extracted from the imported assets.")
    if not profile["typography"]:
        uncertainties.append("No font files or typeface names were found.")
    if not profile["logos"]:
        uncertainties.append("No logo asset was identified with confidence.")
    if text_found:
        for label, value in (
            ("tagline", identity["tagline"]),
            ("brand story", identity["story"]),
            ("positioning", identity["positioning"]),
            ("target audience", identity["audience"]),
            ("brand personality", identity["personality"]),
            ("tone of voice", profile["tone_of_voice"]["tone"]),
            ("photography rules", profile["photography"]["lighting"]),
        ):
            if not value:
                uncertainties.append(
                    f"The PDF did not contain a clear {label}; confirm it with the Owner."
                )
    else:
        uncertainties.append(
            "No readable text was found in the imported PDF. If it is image-only, OCR or a text-based brand book is required."
        )
    profile["uncertainties"] = uncertainties
    return profile


def _chunk_text(text: str, size: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    length = 0
    for paragraph in text.split("\n\n"):
        if current and length + len(paragraph) > size:
            chunks.append("\n\n".join(current))
            current = []
            length = 0
        current.append(paragraph)
        length += len(paragraph) + 2
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def _call_real_analysis(
    brand_name: str,
    text: str,
    chunk_index: int,
    chunk_count: int,
    image_sources: list[AnalysisSource],
) -> dict[str, Any]:
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "Read this excerpt of an existing jewelry brand book and extract EVERY brand rule it contains. "
                f"This is excerpt {chunk_index} of {chunk_count}. "
                "Return ONLY JSON with keys: identity{brand_name,tagline,story,positioning,audience,personality}, "
                "colors[{name,hex,usage}], typography[{family,role}], logos[], "
                "photography{lighting,backgrounds,composition,contrast,shadow_style,retouching,prohibited_styles}, "
                "human_model_style{appearance,makeup,hair,wardrobe,hands_and_nails,posing}, "
                "tone_of_voice{languages,tone,caption_style,emoji_policy,cta_style,hashtag_style}, "
                "graphic_system{patterns,decorative_elements,layout_principles}, "
                "social_media{preferred_ratios,visual_rules,logo_rules}, "
                "additional_sections[{title,content:[strings],page_number,confidence}], dos, donts, uncertainties. "
                "Put any other topic found in the book (packaging, values, mission, materials, care, partnerships, "
                "channels, logo usage, iconography, etc.) into additional_sections with its exact heading. "
                "Use page numbers from the [Page N] markers when known. "
                "Do not invent missing rules; use empty values and list genuine gaps in uncertainties. "
                f"Brand name: {brand_name}.\n\n" + text
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
        timeout=180,
    )
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"]
    if raw.strip().startswith("```"):
        raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("AI response was not an object")
    return parsed


def _merge_profile_value(target: dict[str, Any], key: str, value: Any) -> None:
    existing = target.get(key)
    if isinstance(value, dict):
        if not isinstance(existing, dict):
            target[key] = value
            return
        for child_key, child_value in value.items():
            _merge_profile_value(existing, child_key, child_value)
        return
    if isinstance(value, list):
        merged_list: list[Any] = existing if isinstance(existing, list) else []
        target[key] = merged_list
        for item in value:
            if key == "additional_sections" and isinstance(item, dict):
                title = str(item.get("title", "")).strip()
                match = next(
                    (
                        entry
                        for entry in merged_list
                        if isinstance(entry, dict)
                        and str(entry.get("title", "")).strip().lower() == title.lower()
                    ),
                    None,
                )
                if match:
                    for line in item.get("content", []):
                        if line not in match.setdefault("content", []):
                            match["content"].append(line)
                    continue
            if item not in merged_list:
                merged_list.append(item)
        return
    if isinstance(value, str):
        if not existing or len(value) > len(str(existing)):
            target[key] = value
        return
    if existing in (None, "", [], {}):
        target[key] = value


def _merge_profiles(parts: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for part in parts:
        for key, value in part.items():
            _merge_profile_value(merged, key, value)
    return merged


def _real_analysis(brand_name: str, sources: list[AnalysisSource]) -> dict[str, Any]:
    text_blocks = [
        f"File: {source.filename} ({source.asset_type})\n{source.text or ''}"
        for source in sources
        if source.text
    ]
    full_text = "\n\n".join(text_blocks)
    chunks = _chunk_text(full_text, settings.AI_ANALYSIS_CHUNK_CHARS) or [""]
    truncated = len(chunks) > settings.AI_MAX_ANALYSIS_CHUNKS
    chunks = chunks[: settings.AI_MAX_ANALYSIS_CHUNKS]
    image_sources = [source for source in sources if source.image][:4]

    parts = [
        _call_real_analysis(
            brand_name,
            chunk,
            index + 1,
            len(chunks),
            image_sources if index == 0 else [],
        )
        for index, chunk in enumerate(chunks)
    ]
    merged = _merge_profiles(parts)
    uncertainties = merged.setdefault("uncertainties", [])
    if isinstance(uncertainties, list):
        if truncated:
            uncertainties.append(
                "The brand book was longer than the configured analysis limit; "
                "later pages were not sent to the AI provider."
            )
        if not full_text.strip():
            uncertainties.append(
                "No embedded PDF text was available. Image-only pages require OCR or visual analysis."
            )
    return merged


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


def generate_caption(
    brand_name: str,
    profile_json: dict[str, Any],
    product_name: str,
    category: str,
    metal_color: str | None,
    stone_type: str | None,
) -> dict[str, Any]:
    tone = profile_json.get("tone_of_voice", {})
    identity = profile_json.get("identity", {})
    if settings.AI_PROVIDER == "openai" and settings.AI_API_KEY:
        prompt = (
            f"Write social copy for {brand_name}. Product: {product_name} ({category}), "
            f"metal color: {metal_color or 'unknown'}, stone: {stone_type or 'unknown'}. "
            f"Brand identity: {identity}. Tone rules: {tone}. "
            "Return JSON: {primary_caption, alternatives: [two strings], cta, hashtags: [strings]}. "
            "Respect the brand's language, tone, emoji policy, and CTA style. "
            "Do not invent certifications, prices, or claims."
        )
        response = httpx.post(
            f"{settings.AI_API_BASE.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
            json={
                "model": settings.AI_TEXT_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You write concise premium jewelry captions. Output valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.6,
            },
            timeout=90,
        )
        response.raise_for_status()
        parsed = json.loads(response.json()["choices"][0]["message"]["content"])
        if not isinstance(parsed, dict):
            raise ValueError("Caption response was not an object")
        return parsed

    tagline = identity.get("tagline") or "crafted to be worn"
    primary = (
        f"{product_name}. {tagline}. "
        f"A {category} in {metal_color or 'precious metal'}"
        + (f" with {stone_type}" if stone_type else "")
        + "."
    )
    alternatives = [
        f"Meet the {product_name}: {tagline}.",
        f"Quiet detail, lasting presence. The {product_name} in {metal_color or 'gold'}.",
    ]
    cta = tone.get("cta_style") or "Discover the piece."
    hashtags = [
        f"#{brand_name.replace(' ', '')}",
        f"#{category}",
        "#finejewelry",
    ]
    return {
        "primary_caption": primary,
        "alternatives": alternatives,
        "cta": cta,
        "hashtags": hashtags,
    }
