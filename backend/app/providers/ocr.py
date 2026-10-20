import base64
from typing import Any

import httpx

from app.core.config import settings


class OcrError(Exception):
    pass


def ocr_available() -> bool:
    return bool(settings.OCR_ENABLED and settings.OCR_API_KEY)


def _response_text(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    parts: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                parts.append(content["text"])
            elif content.get("type") == "refusal" and isinstance(content.get("refusal"), str):
                raise OcrError("The OCR model refused to process this document")
    return "\n".join(parts).strip()


def extract_pdf_text(
    pdf_bytes: bytes, filename: str, session_id: str
) -> str:
    """Transcribe a PDF with a vision model through the OpenAI Responses API."""
    if not settings.OCR_ENABLED:
        raise OcrError("OCR is disabled")
    if not settings.OCR_API_KEY:
        raise OcrError("OCR_API_KEY is not configured")
    if len(pdf_bytes) > settings.OCR_MAX_PDF_BYTES:
        raise OcrError(
            f"PDF exceeds the {settings.OCR_MAX_PDF_BYTES // (1024 * 1024)} MB OCR limit"
        )

    encoded = base64.b64encode(pdf_bytes).decode()
    payload = {
        "model": settings.OCR_MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "filename": filename,
                        "file_data": f"data:application/pdf;base64,{encoded}",
                    },
                    {
                        "type": "input_text",
                        "text": (
                            "Transcribe this brand book completely. Preserve headings, "
                            "colors, fonts, tone-of-voice rules, photography rules, model "
                            "direction, social rules, dos/don'ts, and every other section. "
                            "Return plain text only. Start each page with a line containing "
                            "exactly [Page N]. Do not summarize, invent, or omit content."
                        ),
                    },
                ],
            }
        ],
        "max_output_tokens": 40_000,
    }
    headers = {
        "Authorization": f"Bearer {settings.OCR_API_KEY}",
        "User-Agent": "jewelry-brand-studio/1.0",
        "x-opencode-session": session_id,
    }
    try:
        response = httpx.post(
            f"{settings.OCR_API_BASE.rstrip('/')}/responses",
            headers=headers,
            json=payload,
            timeout=240,
        )
        response.raise_for_status()
        payload_json = response.json()
    except OcrError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise OcrError("OCR request failed") from exc

    text = _response_text(payload_json)
    if not text:
        raise OcrError("The OCR model returned no text")
    return text
