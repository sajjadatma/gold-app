import io

from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import settings


def _png(color: tuple[int, int, int], size: tuple[int, int] = (900, 900)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def _setup(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    brand_id = client.post(
        f"{settings.API_V1_STR}/brands", headers=headers, json={"name": "Integrity Brand"}
    ).json()["id"]
    upload = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports",
        headers=headers,
        files=[("files", ("hero.png", _png((160, 120, 70)), "image/png"))],
    )
    profile = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports/{upload.json()['id']}/analyze",
        headers=headers,
    ).json()
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/profile/{profile['id']}/activate",
        headers=headers,
    )
    product = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products",
        headers=headers,
        json={"name": "Ruby Ring", "category": "ring"},
    ).json()
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products/{product['id']}/images",
        headers=headers,
        files=[("file", ("ring.png", _png((150, 110, 60)), "image/png"))],
    )
    return brand_id, product["id"]


def _run(client: TestClient, headers: dict[str, str], brand_id: str, product_id: str) -> dict:
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/generations",
        headers=headers,
        json={"product_id": product_id, "mode": "studio"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_generation_records_integrity_findings(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, product_id = _setup(client, normal_user_token_headers)
    generation = _run(client, normal_user_token_headers, brand_id, product_id)
    asset = generation["assets"][0]
    assert asset["integrity_status"] in {"passed", "needs_review", "failed"}
    assert asset["integrity_findings_json"]["summary"]
    assert asset["integrity_findings_json"]["checks"]


def test_materially_different_output_fails(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    brand_id, product_id = _setup(client, normal_user_token_headers)

    def white_image(*_args, **_kwargs):
        return _png((255, 255, 255), (900, 900))

    monkeypatch.setattr(
        "app.modules.generations.service.generate_image", white_image
    )
    generation = _run(client, normal_user_token_headers, brand_id, product_id)
    assert generation["assets"][0]["integrity_status"] == "failed"


def test_invalid_evaluation_becomes_needs_review(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    brand_id, product_id = _setup(client, normal_user_token_headers)

    monkeypatch.setattr(
        "app.modules.generations.service.evaluate_integrity",
        lambda *_args, **_kwargs: {"status": "totally-fine", "checks": []},
    )
    generation = _run(client, normal_user_token_headers, brand_id, product_id)
    assert generation["assets"][0]["integrity_status"] == "needs_review"
