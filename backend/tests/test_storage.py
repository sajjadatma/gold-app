import uuid
from pathlib import Path

import pytest

from app.providers.storage import (
    LocalStorage,
    StorageError,
    build_storage_key,
    sanitize_filename,
    sha256_hex,
)


def test_local_storage_roundtrip(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    data = b"jewelry brand bytes"
    key = build_storage_key(uuid.uuid4(), "assets", "../../evil.pdf")
    stored = storage.save(key, data, "application/pdf")

    assert stored.checksum == sha256_hex(data)
    assert stored.size_bytes == len(data)
    assert storage.read(key) == data
    assert key.startswith("brands/")
    assert ".." not in key


def test_local_storage_rejects_traversal(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path / "root")
    with pytest.raises(StorageError):
        storage.save("../outside.txt", b"x", "text/plain")


def test_local_storage_delete(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    storage.save("brands/a/file.txt", b"x", "text/plain")
    storage.delete("brands/a/file.txt")
    with pytest.raises(StorageError):
        storage.read("brands/a/file.txt")


def test_filename_sanitization() -> None:
    assert sanitize_filename("../../brand book.pdf") == "brand book.pdf"
    sanitized = sanitize_filename('logo<>:"/\\|?*.svg')
    assert sanitized.endswith(".svg")
    assert not set(sanitized) & set('<>:"/\\|?*')
    assert sanitize_filename("") == "upload"


def test_storage_keys_are_server_generated() -> None:
    brand_id = uuid.uuid4()
    first = build_storage_key(brand_id, "assets", "logo.svg")
    second = build_storage_key(brand_id, "assets", "logo.svg")
    assert first != second
    assert first.startswith(f"brands/{brand_id}/assets/")
