import io

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

from app.core.config import settings
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), (20, 60, 100)).save(buffer, format="PNG")
    return buffer.getvalue()


def _brand(client: TestClient, headers: dict[str, str], name: str = "Atelier") -> str:
    response = client.post(
        f"{settings.API_V1_STR}/brands", headers=headers, json={"name": name}
    )
    assert response.status_code == 200
    return response.json()["id"]


def _profile(
    client: TestClient, headers: dict[str, str], brand_id: str
) -> dict:
    upload = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports",
        headers=headers,
        files=[("files", ("hero.png", _png(), "image/png"))],
    )
    assert upload.status_code == 200, upload.text
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports/{upload.json()['id']}/analyze",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_owner_can_correct_profile(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    profile = _profile(client, normal_user_token_headers, brand_id)
    payload = profile["profile_json"]
    payload["identity"]["tagline"] = "Quietly extraordinary"
    payload["colors"][0]["hex"] = "#C9A227"

    response = client.patch(
        f"{settings.API_V1_STR}/brands/{brand_id}/profile/{profile['id']}",
        headers=normal_user_token_headers,
        json={"profile_json": payload},
    )
    assert response.status_code == 200, response.text
    assert response.json()["profile_json"]["identity"]["tagline"] == "Quietly extraordinary"
    assert response.json()["profile_json"]["colors"][0]["hex"] == "#C9A227"
    assert response.json()["status"] == "needs_review"


def test_invalid_profile_correction_is_rejected(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    profile = _profile(client, normal_user_token_headers, brand_id)
    response = client.patch(
        f"{settings.API_V1_STR}/brands/{brand_id}/profile/{profile['id']}",
        headers=normal_user_token_headers,
        json={"profile_json": {"identity": "wrong", "colors": "gold"}},
    )
    assert response.status_code == 422


def test_content_manager_cannot_edit_or_activate(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    profile = _profile(client, normal_user_token_headers, brand_id)
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
        client.patch(
            f"{settings.API_V1_STR}/brands/{brand_id}/profile/{profile['id']}",
            headers=manager_headers,
            json={"profile_json": profile["profile_json"]},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"{settings.API_V1_STR}/brands/{brand_id}/profile/{profile['id']}/activate",
            headers=manager_headers,
        ).status_code
        == 403
    )


def test_activation_archives_previous_profile(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    first = _profile(client, normal_user_token_headers, brand_id)
    second = _profile(client, normal_user_token_headers, brand_id)

    activated_first = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/profile/{first['id']}/activate",
        headers=normal_user_token_headers,
    )
    assert activated_first.status_code == 200
    assert activated_first.json()["status"] == "active"

    activated_second = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/profile/{second['id']}/activate",
        headers=normal_user_token_headers,
    )
    assert activated_second.status_code == 200
    assert activated_second.json()["status"] == "active"

    profiles = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/profiles",
        headers=normal_user_token_headers,
    ).json()["data"]
    statuses = {item["id"]: item["status"] for item in profiles}
    assert statuses[first["id"]] == "archived"
    assert statuses[second["id"]] == "active"
    assert sum(1 for status in statuses.values() if status == "active") == 1


def test_cannot_activate_another_brands_profile(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    first_brand = _brand(client, normal_user_token_headers, "First")
    second_brand = _brand(client, normal_user_token_headers, "Second")
    profile = _profile(client, normal_user_token_headers, first_brand)
    response = client.post(
        f"{settings.API_V1_STR}/brands/{second_brand}/profile/{profile['id']}/activate",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
