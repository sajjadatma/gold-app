import io
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from PIL import Image
from pypdf import PdfReader
from sqlmodel import Session

from app.core.config import settings
from app.modules.brand_import.models import (
    BrandAsset,
    BrandImport,
    ImportStatus,
    ProcessingStatus,
)
from app.modules.brand_import.validation import (
    ValidationError,
    extension_of,
    extract_zip,
    validate_upload,
)
from app.providers.storage import build_storage_key, get_storage, sanitize_filename


@dataclass
class UploadedInput:
    filename: str
    content_type: str | None
    data: bytes


def _image_metadata(data: bytes) -> dict[str, Any]:
    try:
        image = Image.open(io.BytesIO(data))
        width, height = image.size
        if width * height > settings.MAX_IMAGE_PIXELS:
            raise ValidationError("Image dimensions exceed the safe pixel limit")
        return {"width": width, "height": height, "format": image.format}
    except ValidationError:
        raise
    except Exception as exc:  # noqa: BLE001
        return {"metadata_error": f"Image could not be decoded: {type(exc).__name__}"}


def _pdf_metadata(data: bytes) -> dict[str, Any]:
    try:
        reader = PdfReader(io.BytesIO(data))
        page_count = len(reader.pages)
        page_texts: list[str] = []
        for index, page in enumerate(reader.pages[: settings.MAX_PDF_PAGES]):
            try:
                page_text = (page.extract_text() or "").strip()
            except Exception:  # noqa: BLE001
                page_text = ""
            if page_text:
                page_texts.append(f"[Page {index + 1}]\n{page_text}")
        text = "\n\n".join(page_texts).strip()
        truncated = len(text) > settings.MAX_PDF_TEXT_CHARS
        text = text[: settings.MAX_PDF_TEXT_CHARS]
        return {
            "page_count": page_count,
            "text": text,
            "text_chars": len(text),
            "text_truncated": truncated,
        }
    except Exception as exc:  # noqa: BLE001
        return {"metadata_error": f"PDF could not be parsed: {type(exc).__name__}"}


def extract_metadata(filename: str, data: bytes) -> dict[str, Any]:
    extension = extension_of(filename)
    if extension in {".png", ".jpg", ".jpeg", ".webp"}:
        return _image_metadata(data)
    if extension == ".pdf":
        return _pdf_metadata(data)
    if extension == ".svg":
        return {"format": "svg"}
    return {}


def _store_validated(
    session: Session,
    brand_id: uuid.UUID,
    import_id: uuid.UUID,
    filename: str,
    data: bytes,
    asset_type: str,
    content_type_value: str,
    metadata: dict[str, Any],
) -> BrandAsset:
    key = build_storage_key(brand_id, asset_type, filename)
    stored = get_storage().save(key, data, content_type_value)
    asset = BrandAsset(
        brand_id=brand_id,
        import_id=import_id,
        asset_type=asset_type,
        original_filename=sanitize_filename(filename),
        storage_key=key,
        content_type=content_type_value,
        size_bytes=stored.size_bytes,
        checksum=stored.checksum,
        width=metadata.get("width"),
        height=metadata.get("height"),
        page_count=metadata.get("page_count"),
        metadata_json=metadata,
        processing_status=ProcessingStatus.PROCESSED.value,
    )
    session.add(asset)
    return asset


def process_import(
    session: Session,
    import_row: BrandImport,
    uploads: list[UploadedInput],
) -> BrandImport:
    import_row.status = ImportStatus.PROCESSING.value
    import_row.uploaded_file_count = len(uploads)
    import_row.processed_file_count = 0
    import_row.error_count = 0
    import_row.updated_at = datetime.now(UTC)
    session.add(import_row)
    session.flush()

    processed = 0
    errors = 0

    for upload in uploads:
        try:
            extension = extension_of(upload.filename)
            if extension == ".zip":
                entries = extract_zip(upload.data, upload.filename)
                for name, content in entries:
                    try:
                        validated = validate_upload(name, None, content)
                        metadata = extract_metadata(name, validated.data)
                        _store_validated(
                            session,
                            import_row.brand_id,
                            import_row.id,
                            name,
                            validated.data,
                            validated.asset_type.value,
                            validated.content_type,
                            metadata,
                        )
                        processed += 1
                    except ValidationError:
                        errors += 1
                continue

            validated = validate_upload(
                upload.filename, upload.content_type, upload.data
            )
            if validated.extension == ".zip":
                # Defensive: validate_upload rejects ZIPs, keep the branch explicit.
                errors += 1
                continue
            metadata = extract_metadata(upload.filename, validated.data)
            if "metadata_error" in metadata:
                metadata["warning"] = metadata["metadata_error"]
            _store_validated(
                session,
                import_row.brand_id,
                import_row.id,
                upload.filename,
                validated.data,
                validated.asset_type.value,
                validated.content_type,
                metadata,
            )
            processed += 1
        except ValidationError:
            errors += 1
        except Exception:  # noqa: BLE001
            errors += 1

    import_row.processed_file_count = processed
    import_row.error_count = errors
    if processed == 0:
        import_row.status = ImportStatus.FAILED.value
    elif errors:
        import_row.status = ImportStatus.NEEDS_REVIEW.value
    else:
        import_row.status = ImportStatus.COMPLETED.value
    import_row.updated_at = datetime.now(UTC)
    session.add(import_row)
    session.commit()
    session.refresh(import_row)
    return import_row
