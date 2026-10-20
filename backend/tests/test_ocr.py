import pytest

from app.core.config import settings
from app.providers import ocr
from app.providers.ocr import OcrError, extract_pdf_text, ocr_available


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


def test_ocr_requires_explicit_configuration(monkeypatch) -> None:
    monkeypatch.setattr(settings, "OCR_ENABLED", False)
    monkeypatch.setattr(settings, "OCR_API_KEY", None)
    assert not ocr_available()
    with pytest.raises(OcrError):
        extract_pdf_text(b"%PDF-1.4", "book.pdf", "session")


def test_ocr_calls_responses_api_with_pdf(monkeypatch) -> None:
    monkeypatch.setattr(settings, "OCR_ENABLED", True)
    monkeypatch.setattr(settings, "OCR_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OCR_API_BASE", "https://example.test/v1")
    monkeypatch.setattr(settings, "OCR_MODEL", "gpt-6-luna")
    captured: dict = {}

    def fake_post(url, headers, json, timeout):
        captured.update({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return _FakeResponse(
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": "[Page 1]\nBRAND STORY\nAurum"}
                        ],
                    }
                ]
            }
        )

    monkeypatch.setattr(ocr.httpx, "post", fake_post)
    text = extract_pdf_text(b"%PDF-1.4 sample", "brand-book.pdf", "session-123")

    assert text == "[Page 1]\nBRAND STORY\nAurum"
    assert captured["url"] == "https://example.test/v1/responses"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["headers"]["x-opencode-session"] == "session-123"
    assert captured["json"]["model"] == "gpt-6-luna"
    content = captured["json"]["input"][0]["content"]
    assert content[0]["type"] == "input_file"
    assert content[0]["file_data"].startswith("data:application/pdf;base64,")
    assert content[1]["type"] == "input_text"


def test_ocr_accepts_output_text_helper(monkeypatch) -> None:
    monkeypatch.setattr(settings, "OCR_ENABLED", True)
    monkeypatch.setattr(settings, "OCR_API_KEY", "test-key")
    monkeypatch.setattr(
        ocr.httpx,
        "post",
        lambda *_args, **_kwargs: _FakeResponse({"output_text": "plain transcription"}),
    )
    assert extract_pdf_text(b"%PDF-1.4", "book.pdf", "session") == "plain transcription"
