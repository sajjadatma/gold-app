import io

from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, StreamObject

from app.core.config import settings
from app.modules.brand_import.profile import BrandProfileData
from app.providers.ai import AnalysisSource, analyze_brand

BRAND_BOOK_TEXT = """[Page 1]
AURUM ATELIER

01 BRAND STORY
Aurum Atelier creates quietly luxurious jewelry for people who value craft over noise.

02 BRAND POSITIONING
Modern heirlooms for a considered life.

03 TARGET AUDIENCE
Design-conscious professionals
Collectors of fine jewelry

04 BRAND PERSONALITY
Refined
Warm
Understated

05 TONE OF VOICE
Language: English, Persian
Tone: Warm, elegant, concise
Caption: Short poetic sentences
CTA: Discover the piece
Hashtag: #AurumAtelier

06 PHOTOGRAPHY
Lighting: Soft directional daylight
Backgrounds: Warm ivory, stone
Composition: Generous negative space
Contrast: Low

07 COLORS
Champagne Gold #C9A227
Deep Emerald #0F5132

08 TYPOGRAPHY
Headings: Canela
Body: Inter

09 HUMAN MODEL
Appearance: Minimal, natural
Makeup: Bare skin
Hair: Low chignon
Wardrobe: Ivory silk
Hands and nails: Short nude manicure

10 SOCIAL MEDIA
Ratios: 4:5, 1:1
Visual rules: One hero piece per frame
Logo rules: Logo bottom right

11 DOS
Keep backgrounds warm
Show craftsmanship detail

12 DON'TS
Do not over-style
No neon colors

13 PACKAGING
Ivory box with gold foil monogram
Cotton pouch included

14 SUSTAINABILITY
Recycled gold and responsibly sourced stones
"""


def _text_pdf(text: str) -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    page = writer.pages[0]
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})}
    )
    operations = ["BT", "/F1 12 Tf", "50 740 Td"]
    for index, line in enumerate(text.splitlines()):
        if index:
            operations.append("0 -18 Td")
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        operations.append(f"({safe}) Tj")
    operations.append("ET")
    stream = StreamObject()
    stream.set_data("\n".join(operations).encode())
    page[NameObject("/Contents")] = writer._add_object(stream)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _brand(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        f"{settings.API_V1_STR}/brands", headers=headers, json={"name": "Aurum Atelier"}
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_fake_analysis_parses_brand_book_sections() -> None:
    profile = analyze_brand(
        "Aurum Atelier",
        [
            AnalysisSource(
                filename="brand-book.pdf",
                asset_type="brand_book",
                text=BRAND_BOOK_TEXT,
                asset_id=None,
            )
        ],
    )
    validated = BrandProfileData.model_validate(profile)
    assert validated.identity.story.startswith("Aurum Atelier creates")
    assert validated.identity.positioning == "Modern heirlooms for a considered life."
    assert "Design-conscious professionals" in validated.identity.audience
    assert "Warm" in validated.tone_of_voice.tone
    assert validated.tone_of_voice.cta_style == "Discover the piece"
    assert validated.photography.contrast == "Low"
    assert any(color.hex == "#C9A227" for color in validated.colors)
    assert any(font.family == "Canela" for font in validated.typography)
    assert validated.human_model_style.hair == ["Low chignon"]
    assert validated.social_media.preferred_ratios == ["4:5", "1:1"]
    assert validated.dos and validated.donts
    titles = {section.title for section in validated.additional_sections}
    assert "PACKAGING" in titles
    assert "SUSTAINABILITY" in titles


def test_pdf_upload_analysis_writes_whole_profile(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    pdf = _text_pdf(BRAND_BOOK_TEXT)
    upload = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports",
        headers=normal_user_token_headers,
        files=[("files", ("brand-book.pdf", pdf, "application/pdf"))],
    )
    assert upload.status_code == 200, upload.text
    import_row = upload.json()
    assert import_row["processed_file_count"] == 1
    assert import_row["assets"][0]["page_count"] == 1

    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports/{import_row['id']}/analyze",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200, response.text
    profile = BrandProfileData.model_validate(response.json()["profile_json"])
    assert profile.identity.story
    assert profile.identity.positioning
    assert profile.identity.audience
    assert profile.tone_of_voice.tone
    assert profile.photography.lighting
    assert profile.human_model_style.makeup
    assert profile.graphic_system.layout_principles or profile.social_media.visual_rules
    assert profile.additional_sections
    assert any(section.title == "PACKAGING" for section in profile.additional_sections)


def test_scanned_pdf_uses_ocr_fallback(
    client: TestClient,
    db,
    normal_user_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    from app.core.config import settings as app_settings
    from app.modules.brand_import.models import BrandAsset

    monkeypatch.setattr(app_settings, "OCR_ENABLED", True)
    monkeypatch.setattr(app_settings, "OCR_API_KEY", "test-key")
    calls = {"count": 0}

    def fake_ocr(_pdf: bytes, _filename: str, _session: str) -> str:
        calls["count"] += 1
        return BRAND_BOOK_TEXT

    monkeypatch.setattr(
        "app.modules.brand_import.intelligence.extract_pdf_text", fake_ocr
    )

    brand_id = _brand(client, normal_user_token_headers)
    blank_pdf = _text_pdf("")
    upload = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports",
        headers=normal_user_token_headers,
        files=[("files", ("scanned-book.pdf", blank_pdf, "application/pdf"))],
    )
    assert upload.status_code == 200, upload.text
    import_row = upload.json()
    assert import_row["assets"][0]["content_type"] == "application/pdf"

    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports/{import_row['id']}/analyze",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200, response.text
    profile = BrandProfileData.model_validate(response.json()["profile_json"])
    assert profile.identity.story.startswith("Aurum Atelier")
    assert any(section.title == "PACKAGING" for section in profile.additional_sections)
    assert calls["count"] == 1

    asset = db.get(BrandAsset, import_row["assets"][0]["id"])
    assert asset is not None
    db.refresh(asset)
    assert asset.metadata_json["text"].startswith("[Page 1]")
    assert asset.metadata_json["ocr"]["model"] == app_settings.OCR_MODEL

    # A second analysis reuses the stored OCR text instead of paying again.
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports/{import_row['id']}/analyze",
        headers=normal_user_token_headers,
    )
    assert calls["count"] == 1


def test_uppercase_sections_without_blank_lines_are_preserved() -> None:
    text = (
        "BRAND STORY\nA quiet story.\n"
        "TONE OF VOICE\nWarm, concise.\n"
        "PACKAGING\nIvory box, gold foil.\n"
        "MATERIALS\n18k recycled gold.\n"
    )
    profile = BrandProfileData.model_validate(analyze_brand("Aurum", [
        AnalysisSource(
            filename="book.pdf",
            asset_type="brand_book",
            text=text,
            asset_id=None,
        )
    ]))
    titles = {section.title for section in profile.additional_sections}
    assert {"PACKAGING", "MATERIALS"} <= titles
