import io

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

from app.core.config import settings
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def _png(size: tuple[int, int] = (1200, 1200)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (180, 150, 110)).save(buffer, format="PNG")
    return buffer.getvalue()


def _brand(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        f"{settings.API_V1_STR}/brands", headers=headers, json={"name": "Product Brand"}
    )
    assert response.status_code == 200
    return response.json()["id"]


def _product(client: TestClient, headers: dict[str, str], brand_id: str, name: str = "Gold Ring") -> dict:
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products",
        headers=headers,
        json={
            "name": name,
            "category": "ring",
            "metal_color": "yellow gold",
            "stone_type": "diamond",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_create_and_update_product(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    product = _product(client, normal_user_token_headers, brand_id)
    assert product["category"] == "ring"
    assert product["images"] == []

    updated = client.patch(
        f"{settings.API_V1_STR}/brands/{brand_id}/products/{product['id']}",
        headers=normal_user_token_headers,
        json={"description": "Hand-set brilliant cut", "sku": "R-001"},
    )
    assert updated.status_code == 200
    assert updated.json()["sku"] == "R-001"

    listed = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/products",
        headers=normal_user_token_headers,
    )
    assert listed.json()["count"] == 1


def test_product_category_is_required(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products",
        headers=normal_user_token_headers,
        json={"name": "No category"},
    )
    assert response.status_code == 422


def test_product_images_primary_and_quality(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    product = _product(client, normal_user_token_headers, brand_id)

    first = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products/{product['id']}/images",
        headers=normal_user_token_headers,
        files=[("file", ("ring.png", _png(), "image/png"))],
    )
    assert first.status_code == 200, first.text
    images = first.json()["images"]
    assert len(images) == 1
    assert images[0]["is_primary"] is True
    assert images[0]["quality_status"] == "ok"

    second = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products/{product['id']}/images",
        headers=normal_user_token_headers,
        files=[("file", ("ring-2.png", _png(), "image/png"))],
    )
    assert second.status_code == 200
    assert sum(1 for image in second.json()["images"] if image["is_primary"]) == 1

    second_id = second.json()["images"][1]["id"]
    primary = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products/{product['id']}/images/{second_id}/primary",
        headers=normal_user_token_headers,
    )
    assert primary.status_code == 200
    assert next(
        image for image in primary.json()["images"] if image["id"] == second_id
    )["is_primary"]


def test_low_resolution_image_is_advisory(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    product = _product(client, normal_user_token_headers, brand_id)
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products/{product['id']}/images",
        headers=normal_user_token_headers,
        files=[("file", ("small.png", _png((64, 64)), "image/png"))],
    )
    assert response.status_code == 200
    image = response.json()["images"][0]
    assert image["quality_status"] == "warning"
    assert "low_resolution" in image["quality_findings_json"]["warnings"]


def test_product_image_must_be_raster(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    product = _product(client, normal_user_token_headers, brand_id)
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products/{product['id']}/images",
        headers=normal_user_token_headers,
        files=[("file", ("ring.pdf", b"%PDF-1.4 fake", "application/pdf"))],
    )
    assert response.status_code == 400


def test_archive_product_hides_it_from_default_list(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    product = _product(client, normal_user_token_headers, brand_id)
    archived = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products/{product['id']}/archive",
        headers=normal_user_token_headers,
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    listed = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/products",
        headers=normal_user_token_headers,
    )
    assert listed.json()["count"] == 0
    with_archived = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/products?include_archived=true",
        headers=normal_user_token_headers,
    )
    assert with_archived.json()["count"] == 1


def test_products_are_tenant_isolated(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = _brand(client, normal_user_token_headers)
    product = _product(client, normal_user_token_headers, brand_id)
    other_headers = authentication_token_from_email(
        client=client, email=random_email(), db=db
    )
    assert (
        client.get(
            f"{settings.API_V1_STR}/brands/{brand_id}/products/{product['id']}",
            headers=other_headers,
        ).status_code
        == 404
    )


def test_content_manager_can_manage_products(
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
        f"{settings.API_V1_STR}/brands/{brand_id}/products",
        headers=manager_headers,
        json={"name": "Manager Necklace", "category": "necklace"},
    )
    assert response.status_code == 200
