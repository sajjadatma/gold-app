import io

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

from app.core.config import settings
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def _png(color: tuple[int, int, int] = (170, 140, 100)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (900, 900), color).save(buffer, format="PNG")
    return buffer.getvalue()


def _brand(client: TestClient, headers: dict[str, str], name: str = "Studio Brand") -> str:
    response = client.post(
        f"{settings.API_V1_STR}/brands", headers=headers, json={"name": name}
    )
    assert response.status_code == 200
    return response.json()["id"]


def _activate_profile(client: TestClient, headers: dict[str, str], brand_id: str) -> None:
    upload = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports",
        headers=headers,
        files=[("files", ("hero.png", _png(), "image/png"))],
    )
    assert upload.status_code == 200, upload.text
    profile = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports/{upload.json()['id']}/analyze",
        headers=headers,
    )
    assert profile.status_code == 200, profile.text
    activated = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/profile/{profile.json()['id']}/activate",
        headers=headers,
    )
    assert activated.status_code == 200, activated.text


def _product(client: TestClient, headers: dict[str, str], brand_id: str) -> str:
    product = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products",
        headers=headers,
        json={"name": "Emerald Ring", "category": "ring", "metal_color": "gold"},
    ).json()
    uploaded = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products/{product['id']}/images",
        headers=headers,
        files=[("file", ("ring.png", _png(), "image/png"))],
    )
    assert uploaded.status_code == 200, uploaded.text
    return product["id"]


def _ready_model(client: TestClient, headers: dict[str, str], brand_id: str) -> str:
    model = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models",
        headers=headers,
        json={"type": "virtual", "name": "Aria", "config_json": {"hair": "dark"}},
    ).json()
    generated = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/models/{model['id']}/generate-previews",
        headers=headers,
    )
    assert generated.status_code == 200, generated.text
    return model["id"]


def _generate(
    client: TestClient,
    headers: dict[str, str],
    brand_id: str,
    product_id: str,
    mode: str = "studio",
    model_id: str | None = None,
    aspect_ratio: str = "4:5",
) -> dict:
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/generations",
        headers=headers,
        json={
            "product_id": product_id,
            "mode": mode,
            "aspect_ratio": aspect_ratio,
            "brand_model_id": model_id,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_studio_generation_completes(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    _activate_profile(client, normal_user_token_headers, brand_id)
    product_id = _product(client, normal_user_token_headers, brand_id)

    generation = _generate(client, normal_user_token_headers, brand_id, product_id)
    assert generation["status"] == "completed"
    assert generation["mode"] == "studio"
    assert generation["provider"] in {"fake", "openai"}
    assert len(generation["assets"]) == 1
    asset = generation["assets"][0]
    assert asset["integrity_status"] in {"passed", "needs_review", "failed"}
    assert asset["width"] == 1024 and asset["height"] == 1280

    download = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/generations/assets/{asset['id']}/download",
        headers=normal_user_token_headers,
    )
    assert download.status_code == 200
    assert download.headers["content-type"] == "image/png"


def test_on_model_requires_ready_model(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    _activate_profile(client, normal_user_token_headers, brand_id)
    product_id = _product(client, normal_user_token_headers, brand_id)

    missing = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/generations",
        headers=normal_user_token_headers,
        json={"product_id": product_id, "mode": "on_model"},
    )
    assert missing.status_code == 400

    model_id = _ready_model(client, normal_user_token_headers, brand_id)
    generation = _generate(
        client,
        normal_user_token_headers,
        brand_id,
        product_id,
        mode="on_model",
        model_id=model_id,
    )
    assert generation["status"] == "completed"
    assert generation["brand_model_id"] == model_id


def test_campaign_generation_completes(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    _activate_profile(client, normal_user_token_headers, brand_id)
    product_id = _product(client, normal_user_token_headers, brand_id)
    generation = _generate(
        client,
        normal_user_token_headers,
        brand_id,
        product_id,
        mode="campaign",
        aspect_ratio="1:1",
    )
    assert generation["status"] == "completed"
    assert generation["assets"][0]["width"] == 1024


def test_generation_requires_active_profile(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    product_id = _product(client, normal_user_token_headers, brand_id)
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/generations",
        headers=normal_user_token_headers,
        json={"product_id": product_id, "mode": "studio"},
    )
    assert response.status_code == 400


def test_generation_requires_source_image(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    _activate_profile(client, normal_user_token_headers, brand_id)
    product = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products",
        headers=normal_user_token_headers,
        json={"name": "No photo", "category": "pendant"},
    ).json()
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/generations",
        headers=normal_user_token_headers,
        json={"product_id": product["id"], "mode": "studio"},
    )
    assert response.status_code == 400


def test_generation_is_tenant_isolated(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    _activate_profile(client, normal_user_token_headers, brand_id)
    product_id = _product(client, normal_user_token_headers, brand_id)
    generation = _generate(client, normal_user_token_headers, brand_id, product_id)
    other_headers = authentication_token_from_email(
        client=client, email=random_email(), db=db
    )
    assert (
        client.get(
            f"{settings.API_V1_STR}/brands/{brand_id}/generations/{generation['id']}",
            headers=other_headers,
        ).status_code
        == 404
    )


def test_failed_generation_can_retry(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    _activate_profile(client, normal_user_token_headers, brand_id)
    product_id = _product(client, normal_user_token_headers, brand_id)

    def fail(*_args, **_kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr("app.modules.generations.service.generate_image", fail)
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/generations",
        headers=normal_user_token_headers,
        json={"product_id": product_id, "mode": "studio"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["error_message"]

    monkeypatch.undo()
    retried = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/generations/{response.json()['id']}/retry",
        headers=normal_user_token_headers,
    )
    assert retried.status_code == 200, retried.text
    assert retried.json()["status"] == "completed"
