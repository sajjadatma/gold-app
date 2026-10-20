import io

from PIL import Image

from app.providers.ai import (
    evaluate_integrity,
    generate_image,
    generate_model_previews,
    generate_text,
)


def _png(size: tuple[int, int], color: tuple[int, int, int]) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_fake_image_generation_is_deterministic_and_decodable() -> None:
    source = _png((120, 90), (180, 150, 110))
    first = generate_image("studio jewelry photo", [source], "4:5")
    second = generate_image("studio jewelry photo", [source], "4:5")
    assert first == second
    image = Image.open(io.BytesIO(first))
    assert image.size == (1024, 1280)
    assert image.format == "PNG"


def test_model_previews_generate_requested_count() -> None:
    previews = generate_model_previews("Maison Or", {"age_range": "25-35"}, count=3)
    assert len(previews) == 3
    assert all(Image.open(io.BytesIO(preview)).format == "PNG" for preview in previews)


def test_fake_integrity_passes_identical_images() -> None:
    image = _png((200, 200), (160, 130, 90))
    result = evaluate_integrity(image, image, "Gold ring")
    assert result["status"] == "passed"
    assert result["checks"]


def test_fake_integrity_fails_material_difference() -> None:
    source = _png((200, 200), (0, 0, 0))
    generated = _png((200, 200), (255, 255, 255))
    result = evaluate_integrity(source, generated, "Gold ring")
    assert result["status"] == "failed"


def test_fake_text_provider_is_available_without_credentials() -> None:
    assert generate_text("system", "prompt") == "Fake provider response"
