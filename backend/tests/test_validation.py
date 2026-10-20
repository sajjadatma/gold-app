import io
import zipfile

import pytest
from defusedxml import ElementTree as ET

from app.modules.brand_import.validation import (
    ValidationError,
    extract_zip,
    sanitize_svg,
    validate_upload,
)


def test_svg_sanitization_removes_active_content() -> None:
    raw = b"""<?xml version="1.0"?>
    <svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)">
      <script>alert('xss')</script>
      <a href="https://evil.example"><rect width="10" height="10"/></a>
      <circle cx="5" cy="5" r="4" fill="gold"/>
    </svg>"""
    sanitized = sanitize_svg(raw).decode()
    assert "script" not in sanitized.lower()
    assert "onload" not in sanitized.lower()
    assert "evil.example" not in sanitized
    assert "circle" in sanitized
    assert ET.fromstring(sanitized) is not None


def test_svg_with_doctype_is_rejected() -> None:
    raw = b'<!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><svg/>'
    with pytest.raises(ValidationError):
        sanitize_svg(raw)


def test_extension_mime_mismatch_rejected() -> None:
    with pytest.raises(ValidationError):
        validate_upload("logo.png", "application/pdf", b"%PDF-1.4 fake")


def test_signature_mismatch_rejected() -> None:
    with pytest.raises(ValidationError):
        validate_upload("logo.png", "image/png", b"not a png at all")


def test_zip_traversal_rejected() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("../escape.png", b"x")
    with pytest.raises(ValidationError):
        extract_zip(buffer.getvalue(), "bundle.zip")


def test_zip_symlink_rejected() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        info = zipfile.ZipInfo("link.png")
        info.external_attr = 0o120777 << 16
        archive.writestr(info, b"x")
    with pytest.raises(ValidationError):
        extract_zip(buffer.getvalue(), "bundle.zip")


def test_zip_nested_archive_rejected() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("inner.zip", b"PK\x03\x04")
    with pytest.raises(ValidationError):
        extract_zip(buffer.getvalue(), "bundle.zip")


def test_zip_expansion_and_count_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for index in range(3):
            archive.writestr(f"file{index}.svg", b"<svg/>")
    from app.core import config

    monkeypatch.setattr(config.settings, "MAX_ARCHIVE_FILES", 2)
    with pytest.raises(ValidationError):
        extract_zip(buffer.getvalue(), "bundle.zip")


def test_svg_external_and_data_references_removed() -> None:
    raw = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <image href="https://tracker.example/pixel.png"/>
      <use href="data:image/svg+xml;base64,PHN2Zz48c2NyaXB0PmFsZXJ0KDEpPC9zY3JpcHQ+PC9zdmc+"/>
      <rect href="#safe" width="10" height="10"/>
    </svg>"""
    sanitized = sanitize_svg(raw).decode()
    assert "tracker.example" not in sanitized
    assert "data:image" not in sanitized
    assert "#safe" in sanitized


def test_svg_style_elements_removed() -> None:
    raw = b'<svg xmlns="http://www.w3.org/2000/svg"><style>rect{fill:url(javascript:1)}</style><rect width="2" height="2"/></svg>'
    sanitized = sanitize_svg(raw).decode()
    assert "<style" not in sanitized
