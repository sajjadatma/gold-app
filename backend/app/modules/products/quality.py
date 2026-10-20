import io
from dataclasses import dataclass, field
from typing import Any

from PIL import Image, ImageFilter, ImageStat

from app.core.config import settings


@dataclass
class QualityResult:
    width: int
    height: int
    status: str = "ok"
    findings: dict[str, Any] = field(default_factory=dict)


def analyze_product_image(data: bytes) -> QualityResult:
    try:
        image = Image.open(io.BytesIO(data))
        width, height = image.size
        if width * height > settings.MAX_IMAGE_PIXELS:
            raise ValueError("Image dimensions exceed the safe pixel limit")
        grayscale = image.convert("L")
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Image could not be decoded") from exc

    findings: dict[str, Any] = {}
    warnings: list[str] = []

    if min(width, height) < 800:
        warnings.append("low_resolution")
    ratio = width / max(height, 1)
    if ratio > 4 or ratio < 0.25:
        warnings.append("unusable_crop")

    brightness = ImageStat.Stat(grayscale).mean[0]
    findings["brightness"] = round(brightness, 1)
    if brightness < 30:
        warnings.append("underexposed")
    elif brightness > 235:
        warnings.append("overexposed")

    edges = grayscale.filter(ImageFilter.FIND_EDGES)
    edge_variance = ImageStat.Stat(edges).stddev[0]
    findings["edge_variance"] = round(edge_variance, 1)
    if edge_variance < 8:
        warnings.append("likely_blurred")

    findings["warnings"] = warnings
    return QualityResult(
        width=width,
        height=height,
        status="warning" if warnings else "ok",
        findings=findings,
    )
