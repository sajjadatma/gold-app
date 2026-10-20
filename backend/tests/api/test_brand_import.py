import io
import uuid
import zipfile

from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfWriter
from sqlmodel import Session

from app.core.config import settings
from app.modules.brand_import import validation
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), (120, 90, 30)).save(buffer, format="PNG")
    return buffer.getvalue()


def _pdf() -> bytes:
    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.write(buffer)
    return buffer.getvalue()


def _zip(entries: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def _brand(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        f"{settings.API_V1_STR}/brands", headers=headers, json={"name": "Import Test"}
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _upload(
    client: TestClient,
    headers: dict[str, str],
    brand_id: str,
    files: list[tuple[str, tuple[str, bytes, str]]],
) -> dict:
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports",
        headers=headers,
        files=files,
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_import_realistic_bundle(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    result = _upload(
        client,
        normal_user_token_headers,
        brand_id,
        [
            ("files", ("brand-book.pdf", _pdf(), "application/pdf")),
            ("files", ("ring.png", _png(), "image/png")),
            ("files", ("logo.svg", b"<svg xmlns='http://www.w3.org/2000/svg'/>", "image/svg+xml")),
            ("files", ("serif.ttf", b"\x00\x01\x00\x00" + b"font" * 10, "font/ttf")),
        ],
    )
    assert result["status"] == "completed"
    assert result["processed_file_count"] == 4
    assert result["error_count"] == 0
    by_name = {asset["original_filename"]: asset for asset in result["assets"]}
    assert by_name["ring.png"]["width"] == 64
    assert by_name["ring.png"]["height"] == 48
    assert by_name["brand-book.pdf"]["page_count"] == 1
    assert by_name["serif.ttf"]["asset_type"] == "font"
    assert by_name["logo.svg"]["asset_type"] == "graphic_element"

    listed = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/assets",
        headers=normal_user_token_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["count"] == 4

    filtered = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/assets?asset_type=image",
        headers=normal_user_token_headers,
    )
    assert filtered.json()["count"] == 1


def test_import_rejects_mime_mismatch(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    result = _upload(
        client,
        normal_user_token_headers,
        brand_id,
        [("files", ("brand-book.png", _pdf(), "application/pdf"))],
    )
    assert result["status"] == "failed"
    assert result["error_count"] == 1
    assert result["assets"] == []


def test_import_rejects_unsupported_extension(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    result = _upload(
        client,
        normal_user_token_headers,
        brand_id,
        [("files", ("payload.exe", b"MZ...", "application/octet-stream"))],
    )
    assert result["status"] == "failed"
    assert result["error_count"] == 1


def test_import_rejects_size_limit(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    monkeypatch.setitem(validation.SIZE_LIMITS, ".png", 10)
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports",
        headers=normal_user_token_headers,
        files=[("files", ("huge.png", _png(), "image/png"))],
    )
    assert response.status_code == 413


def test_import_zip_bundle(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    result = _upload(
        client,
        normal_user_token_headers,
        brand_id,
        [("files", ("bundle.zip", _zip({"logo.png": _png()}), "application/zip"))],
    )
    assert result["status"] == "completed"
    assert result["processed_file_count"] == 1


def test_import_zip_traversal_fails_without_writing(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    result = _upload(
        client,
        normal_user_token_headers,
        brand_id,
        [("files", ("evil.zip", _zip({"../evil.png": _png()}), "application/zip"))],
    )
    assert result["status"] == "failed"
    assert result["assets"] == []


def test_svg_script_is_removed_before_storage(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    raw = b"""<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)">
      <script>alert('xss')</script><rect width="10" height="10"/></svg>"""
    result = _upload(
        client,
        normal_user_token_headers,
        brand_id,
        [("files", ("logo.svg", raw, "image/svg+xml"))],
    )
    asset_id = result["assets"][0]["id"]
    preview = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/assets/{asset_id}/preview",
        headers=normal_user_token_headers,
    )
    assert preview.status_code == 200
    assert b"script" not in preview.content.lower()
    assert b"onload" not in preview.content.lower()


def test_import_is_tenant_isolated(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    result = _upload(
        client,
        normal_user_token_headers,
        brand_id,
        [("files", ("ring.png", _png(), "image/png"))],
    )
    asset_id = result["assets"][0]["id"]
    other_headers = authentication_token_from_email(
        client=client, email=random_email(), db=db
    )
    assert (
        client.get(
            f"{settings.API_V1_STR}/brands/{brand_id}/imports/{result['id']}",
            headers=other_headers,
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"{settings.API_V1_STR}/brands/{brand_id}/assets/{asset_id}/preview",
            headers=other_headers,
        ).status_code
        == 404
    )


def test_only_owner_can_archive_asset(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    result = _upload(
        client,
        normal_user_token_headers,
        brand_id,
        [("files", ("ring.png", _png(), "image/png"))],
    )
    asset_id = result["assets"][0]["id"]
    manager_email = random_email()
    manager_headers = authentication_token_from_email(
        client=client, email=manager_email, db=db
    )
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/members",
        headers=normal_user_token_headers,
        json={"email": manager_email, "role": "content_manager"},
    )
    assert (
        client.delete(
            f"{settings.API_V1_STR}/brands/{brand_id}/assets/{asset_id}",
            headers=manager_headers,
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"{settings.API_V1_STR}/brands/{brand_id}/assets/{asset_id}",
            headers=normal_user_token_headers,
        ).status_code
        == 200
    )
    active = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/assets",
        headers=normal_user_token_headers,
    )
    assert active.json()["count"] == 0


def test_import_id_is_uuid(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    result = _upload(
        client,
        normal_user_token_headers,
        brand_id,
        [("files", ("ring.png", _png(), "image/png"))],
    )
    uuid.UUID(result["id"])
