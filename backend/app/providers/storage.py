import hashlib
import re
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.config import settings


class StorageError(Exception):
    pass


@dataclass(frozen=True)
class StoredObject:
    key: str
    checksum: str
    size_bytes: int
    content_type: str


def safe_extension(filename: str, fallback: str = ".bin") -> str:
    match = re.search(r"(\.[A-Za-z0-9]{1,10})$", filename.strip())
    return match.group(1).lower() if match else fallback


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip(" .")
    return name[:255] or "upload"


def build_storage_key(brand_id: uuid.UUID, namespace: str, filename: str) -> str:
    """Server-generated, tenant-prefixed key. Never derived from user paths."""
    safe_namespace = re.sub(r"[^a-z0-9_-]", "", namespace.lower()) or "files"
    return f"brands/{brand_id}/{safe_namespace}/{uuid.uuid4().hex}{safe_extension(filename)}"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root.resolve()):
            raise StorageError("Invalid storage key")
        return path

    def save(self, key: str, data: bytes, content_type: str) -> StoredObject:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return StoredObject(
            key=key,
            checksum=sha256_hex(data),
            size_bytes=len(data),
            content_type=content_type,
        )

    def read(self, key: str) -> bytes:
        path = self._path(key)
        if not path.is_file():
            raise StorageError("Object not found")
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.is_file():
            path.unlink()


class S3Storage:
    """Thin S3-compatible adapter; configured only for production."""

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None,
        access_key_id: str | None,
        secret_access_key: str | None,
        region: str,
    ) -> None:
        import boto3  # type: ignore[import-untyped]

        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
        )

    def save(self, key: str, data: bytes, content_type: str) -> StoredObject:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return StoredObject(
            key=key,
            checksum=sha256_hex(data),
            size_bytes=len(data),
            content_type=content_type,
        )

    def read(self, key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return bytes(response["Body"].read())
        except Exception as exc:  # noqa: BLE001
            raise StorageError("Object not found") from exc

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


@lru_cache
def get_storage() -> LocalStorage | S3Storage:
    if settings.STORAGE_BACKEND == "s3":
        if not settings.S3_BUCKET:
            raise StorageError("S3_BUCKET is required for the S3 storage backend")
        return S3Storage(
            bucket=settings.S3_BUCKET,
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key_id=settings.S3_ACCESS_KEY_ID,
            secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region=settings.S3_REGION,
        )
    return LocalStorage(Path(settings.STORAGE_LOCAL_DIR))
