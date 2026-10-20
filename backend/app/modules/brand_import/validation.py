import io
import os
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath

from defusedxml import ElementTree as DefusedET  # type: ignore[import-untyped]

from app.core.config import settings
from app.modules.brand_import.models import AssetType


class ValidationError(Exception):
    pass


@dataclass(frozen=True)
class ValidatedFile:
    filename: str
    extension: str
    asset_type: AssetType
    content_type: str
    data: bytes


EXTENSION_TYPES: dict[str, AssetType] = {
    ".pdf": AssetType.BRAND_BOOK,
    ".png": AssetType.IMAGE,
    ".jpg": AssetType.IMAGE,
    ".jpeg": AssetType.IMAGE,
    ".webp": AssetType.IMAGE,
    ".svg": AssetType.GRAPHIC_ELEMENT,
    ".ttf": AssetType.FONT,
    ".otf": AssetType.FONT,
    ".woff": AssetType.FONT,
    ".woff2": AssetType.FONT,
    ".zip": AssetType.OTHER,
    ".ai": AssetType.DESIGN_SOURCE,
    ".eps": AssetType.DESIGN_SOURCE,
    ".psd": AssetType.DESIGN_SOURCE,
}

CONTENT_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".zip": "application/zip",
    ".ai": "application/postscript",
    ".eps": "application/postscript",
    ".psd": "image/vnd.adobe.photoshop",
}

ALLOWED_MIMES: dict[str, set[str]] = {
    ".pdf": {"application/pdf"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg", "image/jpg"},
    ".jpeg": {"image/jpeg", "image/jpg"},
    ".webp": {"image/webp"},
    ".svg": {"image/svg+xml", "text/xml", "application/xml"},
    ".ttf": {"font/ttf", "application/x-font-ttf", "application/octet-stream"},
    ".otf": {"font/otf", "application/x-font-otf", "application/octet-stream"},
    ".woff": {"font/woff", "application/font-woff", "application/octet-stream"},
    ".woff2": {"font/woff2", "application/octet-stream"},
    ".zip": {"application/zip", "application/x-zip-compressed"},
    ".ai": {"application/postscript", "application/pdf", "application/illustrator"},
    ".eps": {"application/postscript", "application/eps"},
    ".psd": {"image/vnd.adobe.photoshop", "application/octet-stream"},
}

SIZE_LIMITS: dict[str, int] = {
    ".pdf": settings.MAX_PDF_BYTES,
    ".png": settings.MAX_IMAGE_BYTES,
    ".jpg": settings.MAX_IMAGE_BYTES,
    ".jpeg": settings.MAX_IMAGE_BYTES,
    ".webp": settings.MAX_IMAGE_BYTES,
    ".svg": settings.MAX_IMAGE_BYTES,
    ".ttf": settings.MAX_FONT_BYTES,
    ".otf": settings.MAX_FONT_BYTES,
    ".woff": settings.MAX_FONT_BYTES,
    ".woff2": settings.MAX_FONT_BYTES,
    ".zip": settings.MAX_ZIP_BYTES,
    ".ai": settings.MAX_DESIGN_SOURCE_BYTES,
    ".eps": settings.MAX_DESIGN_SOURCE_BYTES,
    ".psd": settings.MAX_DESIGN_SOURCE_BYTES,
}


def extension_of(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def limit_for(filename: str) -> int:
    return SIZE_LIMITS.get(extension_of(filename), settings.MAX_IMAGE_BYTES)


def _looks_like_svg(data: bytes) -> bool:
    head = data[:1024].lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    return head.startswith(b"<svg") or (head.startswith(b"<?xml") and b"<svg" in head)


def _check_signature(extension: str, data: bytes, filename: str) -> None:
    head = data[:16]
    if extension == ".pdf" and not data.startswith(b"%PDF-"):
        raise ValidationError(f"{filename}: not a valid PDF")
    if extension == ".png" and not head.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValidationError(f"{filename}: not a valid PNG")
    if extension in {".jpg", ".jpeg"} and not head.startswith(b"\xff\xd8\xff"):
        raise ValidationError(f"{filename}: not a valid JPEG")
    if extension == ".webp" and not (head.startswith(b"RIFF") and head[8:12] == b"WEBP"):
        raise ValidationError(f"{filename}: not a valid WebP")
    if extension == ".svg" and not _looks_like_svg(data):
        raise ValidationError(f"{filename}: not a valid SVG")
    if extension in {".ttf", ".otf", ".woff", ".woff2"}:
        valid = head.startswith(
            (b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf", b"wOFF", b"wOF2")
        )
        if not valid:
            raise ValidationError(f"{filename}: not a valid font")
    if extension == ".zip" and not head.startswith((b"PK\x03\x04", b"PK\x05\x06")):
        raise ValidationError(f"{filename}: not a valid ZIP archive")
    if extension == ".psd" and not data.startswith(b"8BPS"):
        raise ValidationError(f"{filename}: not a valid PSD file")
    if extension in {".ai", ".eps"} and not data.startswith((b"%!PS", b"%PDF-")):
        raise ValidationError(f"{filename}: not a valid AI/EPS file")


def validate_upload(
    filename: str, declared_content_type: str | None, data: bytes
) -> ValidatedFile:
    extension = extension_of(filename)
    if extension == ".zip":
        raise ValidationError("ZIP archives must be expanded by the import service")
    asset_type = EXTENSION_TYPES.get(extension)
    if not asset_type:
        raise ValidationError(f"{filename}: unsupported file type")

    limit = limit_for(filename)
    if len(data) > limit:
        raise ValidationError(f"{filename}: file exceeds {limit // (1024 * 1024)} MB limit")
    if not data:
        raise ValidationError(f"{filename}: file is empty")

    declared = (declared_content_type or "").split(";")[0].strip().lower()
    allowed = ALLOWED_MIMES[extension]
    if declared and declared not in allowed and declared != "application/octet-stream":
        raise ValidationError(f"{filename}: content type does not match extension")

    _check_signature(extension, data, filename)
    # SVG is validated at the XML level and stored sanitized before rendering.
    if extension == ".svg":
        data = sanitize_svg(data)

    return ValidatedFile(
        filename=filename,
        extension=extension,
        asset_type=asset_type,
        content_type=CONTENT_TYPES[extension],
        data=data,
    )


def sanitize_svg(data: bytes) -> bytes:
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValidationError("SVG: DTD/entity declarations are not allowed")
    try:
        root = DefusedET.fromstring(data)
    except Exception as exc:  # noqa: BLE001
        raise ValidationError("SVG: could not be parsed safely") from exc

    forbidden = {"script", "foreignobject", "iframe", "object", "embed", "audio", "video"}
    for element in list(root.iter()):
        tag = element.tag.split("}")[-1].lower()
        if tag in forbidden:
            element.clear()
            parent = _find_parent(root, element)
            if parent is not None:
                parent.remove(element)
            continue
        for attribute in list(element.attrib):
            local = attribute.split("}")[-1].lower()
            value = element.attrib[attribute].strip().lower()
            if local.startswith("on") or (
                local in {"href", "src"} and not value.startswith(("#", "data:image/"))
            ):
                del element.attrib[attribute]

    return bytes(DefusedET.tostring(root, encoding="utf-8"))


def _find_parent(root: DefusedET.Element, target: DefusedET.Element) -> DefusedET.Element | None:
    for parent in root.iter():
        for child in list(parent):
            if child is target:
                return parent
    return None


def extract_zip(data: bytes, archive_name: str) -> list[tuple[str, bytes]]:
    """Return (filename, bytes) for safe entries. Reject traversal/symlinks/bombs."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ValidationError(f"{archive_name}: invalid ZIP archive") from exc

    infos = archive.infolist()
    if len(infos) > settings.MAX_ARCHIVE_FILES:
        raise ValidationError(
            f"{archive_name}: archive contains more than {settings.MAX_ARCHIVE_FILES} files"
        )
    if any(info.flag_bits & 0x1 for info in infos):
        raise ValidationError(f"{archive_name}: encrypted archives are not supported")
    expanded = sum(info.file_size for info in infos)
    if expanded > settings.MAX_ARCHIVE_EXPANDED_BYTES:
        raise ValidationError(f"{archive_name}: archive expands beyond the size limit")

    entries: list[tuple[str, bytes]] = []
    total_read = 0
    for info in infos:
        if info.is_dir():
            continue
        name = info.filename.replace("\\", "/")
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValidationError(f"{archive_name}: unsafe archive path")
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValidationError(f"{archive_name}: symlinks are not allowed")
        extension = extension_of(name)
        if extension == ".zip":
            raise ValidationError(f"{archive_name}: nested archives are not supported")
        if extension not in EXTENSION_TYPES:
            continue
        with archive.open(info) as handle:
            content = handle.read(limit_for(name) + 1)
        total_read += len(content)
        if total_read > settings.MAX_ARCHIVE_EXPANDED_BYTES:
            raise ValidationError(f"{archive_name}: archive expands beyond the size limit")
        if len(content) > limit_for(name):
            raise ValidationError(f"{archive_name}: {name} exceeds its size limit")
        entries.append((path.name, content))
    return entries
