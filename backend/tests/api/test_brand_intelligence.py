import io

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

from app.core.config import settings
from app.modules.brand_import.profile import BrandProfileData
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def _png(color: tuple[int, int, int] = (120, 90, 30)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), color).save(buffer, format="PNG")
    return buffer.getvalue()


def _brand(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        f"{settings.API_V1_STR}/brands", headers=headers, json={"name": "Maison Or"}
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _import_fixture(
    client: TestClient, headers: dict[str, str], brand_id: str
) -> dict:
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports",
        headers=headers,
        files=[
            ("files", ("hero.png", _png(), "image/png")),
            ("files", ("MaisonSerif.ttf", b"\x00\x01\x00\x00" + b"f" * 20, "font/ttf")),
            ("files", ("logo.svg", b"<svg xmlns='http://www.w3.org/2000/svg'/>", "image/svg+xml")),
        ],
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_analysis_produces_validated_profile(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    import_row = _import_fixture(client, normal_user_token_headers, brand_id)

    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports/{import_row['id']}/analyze",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200, response.text
    profile = response.json()
    assert profile["status"] == "needs_review"
    assert profile["version"] == 1
    validated = BrandProfileData.model_validate(profile["profile_json"])
    assert validated.identity.brand_name == "Maison Or"
    assert validated.colors
    assert any(font.family == "MaisonSerif" for font in validated.typography)
    assert validated.logos
    assert validated.uncertainties
    # The fake provider never invents a tagline.
    assert validated.identity.tagline == ""

    latest = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/profile",
        headers=normal_user_token_headers,
    )
    assert latest.status_code == 200
    assert latest.json()["id"] == profile["id"]


def test_second_analysis_increments_version(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    import_row = _import_fixture(client, normal_user_token_headers, brand_id)
    first = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports/{import_row['id']}/analyze",
        headers=normal_user_token_headers,
    )
    second = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports/{import_row['id']}/analyze",
        headers=normal_user_token_headers,
    )
    assert first.json()["version"] == 1
    assert second.json()["version"] == 2


def test_invalid_ai_output_is_not_persisted(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    import_row = _import_fixture(client, normal_user_token_headers, brand_id)

    monkeypatch.setattr(
        "app.modules.brand_import.intelligence.analyze_brand",
        lambda *_args, **_kwargs: {"colors": "not-a-list", "identity": "wrong"},
    )
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports/{import_row['id']}/analyze",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 502
    profiles = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/profiles",
        headers=normal_user_token_headers,
    )
    assert profiles.json()["count"] == 0


def test_analysis_requires_assets(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    failed_import = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports",
        headers=normal_user_token_headers,
        files=[("files", ("bad.exe", b"MZ", "application/octet-stream"))],
    )
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports/{failed_import.json()['id']}/analyze",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 502


def test_analysis_is_tenant_isolated(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    import_row = _import_fixture(client, normal_user_token_headers, brand_id)
    other_headers = authentication_token_from_email(
        client=client, email=random_email(), db=db
    )
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports/{import_row['id']}/analyze",
        headers=other_headers,
    )
    assert response.status_code == 404
    profiles = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/profiles",
        headers=normal_user_token_headers,
    )
    assert profiles.json()["count"] == 0
