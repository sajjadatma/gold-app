import io

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

from app.core.config import settings
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def _png(color: tuple[int, int, int] = (150, 120, 90)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (48, 64), color).save(buffer, format="PNG")
    return buffer.getvalue()


def _brand(client: TestClient, headers: dict[str, str], name: str = "Model Brand") -> str:
    response = client.post(
        f"{settings.API_V1_STR}/brands", headers=headers, json={"name": name}
    )
    assert response.status_code == 200
    return response.json()["id"]


def _create_model(client: TestClient, headers: dict[str, str], brand_id: str, type_: str, name: str = "Aria") -> dict:
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models",
        headers=headers,
        json={"type": type_, "name": name, "config_json": {"age_range": "25-35"}},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_virtual_model_reaches_ready_and_default(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    model = _create_model(client, normal_user_token_headers, brand_id, "virtual")
    assert model["status"] == "draft"

    previews = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}/generate-previews",
        headers=normal_user_token_headers,
    )
    assert previews.status_code == 200, previews.text
    detail = previews.json()
    assert detail["status"] == "ready"
    assert len(detail["references"]) == 3
    assert sum(1 for ref in detail["references"] if ref["is_canonical"]) == 1

    default = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}/default",
        headers=normal_user_token_headers,
    )
    assert default.status_code == 200
    assert default.json()["is_default"] is True


def test_real_model_requires_consent(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    model = _create_model(client, normal_user_token_headers, brand_id, "real", "Noor")

    upload = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}/references",
        headers=normal_user_token_headers,
        files=[("file", ("noor.png", _png(), "image/png"))],
    )
    assert upload.status_code == 200, upload.text
    assert upload.json()["status"] == "draft"
    assert len(upload.json()["references"]) == 1

    blocked = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}/default",
        headers=normal_user_token_headers,
    )
    assert blocked.status_code == 400

    consent = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}/consent",
        headers=normal_user_token_headers,
        json={
            "confirmation_text_version": "2026-01",
            "permission_scope": "brand_imagery",
        },
    )
    assert consent.status_code == 200, consent.text
    assert consent.json()["status"] == "ready"
    assert consent.json()["consent"]["permission_scope"] == "brand_imagery"

    default = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}/default",
        headers=normal_user_token_headers,
    )
    assert default.status_code == 200
    assert default.json()["is_default"] is True


def test_real_model_consent_requires_reference(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    model = _create_model(client, normal_user_token_headers, brand_id, "real")
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}/consent",
        headers=normal_user_token_headers,
        json={"confirmation_text_version": "1", "permission_scope": "brand"},
    )
    assert response.status_code == 400


def test_virtual_model_cannot_record_consent(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    model = _create_model(client, normal_user_token_headers, brand_id, "virtual")
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}/consent",
        headers=normal_user_token_headers,
        json={"confirmation_text_version": "1", "permission_scope": "brand"},
    )
    assert response.status_code == 400


def test_real_model_previews_are_rejected(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    model = _create_model(client, normal_user_token_headers, brand_id, "real")
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}/generate-previews",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400


def test_reference_must_be_an_image(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    model = _create_model(client, normal_user_token_headers, brand_id, "real")
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}/references",
        headers=normal_user_token_headers,
        files=[("file", ("book.pdf", b"%PDF-1.4 fake", "application/pdf"))],
    )
    assert response.status_code == 400


def test_only_one_default_model(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    first = _create_model(client, normal_user_token_headers, brand_id, "virtual", "One")
    second = _create_model(client, normal_user_token_headers, brand_id, "virtual", "Two")
    for model in (first, second):
        client.post(
            f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}/generate-previews",
            headers=normal_user_token_headers,
        )
        client.post(
            f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}/default",
            headers=normal_user_token_headers,
        )
    models = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/models",
        headers=normal_user_token_headers,
    ).json()["data"]
    assert sum(1 for model in models if model["is_default"]) == 1


def test_models_are_tenant_isolated(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    model = _create_model(client, normal_user_token_headers, brand_id, "virtual")
    other_headers = authentication_token_from_email(
        client=client, email=random_email(), db=db
    )
    assert (
        client.get(
            f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}",
            headers=other_headers,
        ).status_code
        == 404
    )


def test_content_manager_can_manage_models(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    manager_email = random_email()
    manager_headers = authentication_token_from_email(
        client=client, email=manager_email, db=db
    )
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/members",
        headers=normal_user_token_headers,
        json={"email": manager_email, "role": "content_manager"},
    )
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models",
        headers=manager_headers,
        json={"type": "virtual", "name": "Manager Model"},
    )
    assert response.status_code == 200
