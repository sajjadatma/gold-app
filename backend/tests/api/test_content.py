import io

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

from app.core.config import settings
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (900, 900), (165, 130, 90)).save(buffer, format="PNG")
    return buffer.getvalue()


def _setup(client: TestClient, headers: dict[str, str]) -> tuple[str, str, str]:
    brand_id = client.post(
        f"{settings.API_V1_STR}/brands", headers=headers, json={"name": "Caption Brand"}
    ).json()["id"]
    upload = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/imports",
        headers=headers,
        files=[("files", ("hero.png", _png(), "image/png"))],
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
        json={"name": "Pearl Drop", "category": "earrings", "metal_color": "gold"},
    ).json()
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products/{product['id']}/images",
        headers=headers,
        files=[("file", ("ring.png", _png(), "image/png"))],
    )
    generation = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/generations",
        headers=headers,
        json={"product_id": product["id"], "mode": "studio"},
    ).json()
    return brand_id, product["id"], generation["assets"][0]["id"]


def _draft(client: TestClient, headers: dict[str, str], brand_id: str, asset_id: str) -> dict:
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts",
        headers=headers,
        json={"generated_asset_id": asset_id},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_generate_caption_fills_draft(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, product_id, asset_id = _setup(client, normal_user_token_headers)
    draft = _draft(client, normal_user_token_headers, brand_id, asset_id)
    assert draft["caption"] == ""
    assert draft["status"] == "draft"

    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/generate-caption",
        headers=normal_user_token_headers,
        json={},
    )
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["caption"]
    assert len(content["alternative_captions_json"]) == 2
    assert content["cta"]
    assert content["hashtags"]
    assert content["user_edited"] is False
    assert content["product_id"] == product_id
    assert content["integrity_status"] in {"passed", "needs_review", "failed"}
    assert content["brand_profile_version"] == 1


def test_manual_edit_is_not_silently_overwritten(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, _product_id, asset_id = _setup(client, normal_user_token_headers)
    draft = _draft(client, normal_user_token_headers, brand_id, asset_id)
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/generate-caption",
        headers=normal_user_token_headers,
        json={},
    )
    edited = client.patch(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}",
        headers=normal_user_token_headers,
        json={"caption": "My own carefully written caption."},
    )
    assert edited.status_code == 200
    assert edited.json()["user_edited"] is True

    blocked = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/generate-caption",
        headers=normal_user_token_headers,
        json={},
    )
    assert blocked.status_code == 409
    current = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}",
        headers=normal_user_token_headers,
    ).json()
    assert current["caption"] == "My own carefully written caption."

    forced = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/generate-caption",
        headers=normal_user_token_headers,
        json={"force": True},
    )
    assert forced.status_code == 200
    assert forced.json()["caption"] != "My own carefully written caption."


def test_invalid_caption_output_keeps_existing_text(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    brand_id, _product_id, asset_id = _setup(client, normal_user_token_headers)
    draft = _draft(client, normal_user_token_headers, brand_id, asset_id)
    client.patch(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}",
        headers=normal_user_token_headers,
        json={"caption": "Keep me"},
    )
    monkeypatch.setattr(
        "app.modules.content.service.generate_caption",
        lambda *_args, **_kwargs: {"primary_caption": "", "alternatives": []},
    )
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/generate-caption",
        headers=normal_user_token_headers,
        json={"force": True},
    )
    assert response.status_code == 400
    current = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}",
        headers=normal_user_token_headers,
    ).json()
    assert current["caption"] == "Keep me"


def test_submit_requires_caption(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, _product_id, asset_id = _setup(client, normal_user_token_headers)
    draft = _draft(client, normal_user_token_headers, brand_id, asset_id)
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/submit",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400

    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/generate-caption",
        headers=normal_user_token_headers,
        json={},
    )
    submitted = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/submit",
        headers=normal_user_token_headers,
    )
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "needs_approval"


def test_drafts_are_tenant_isolated(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, _product_id, asset_id = _setup(client, normal_user_token_headers)
    draft = _draft(client, normal_user_token_headers, brand_id, asset_id)
    other_headers = authentication_token_from_email(
        client=client, email=random_email(), db=db
    )
    assert (
        client.get(
            f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}",
            headers=other_headers,
        ).status_code
        == 404
    )


def test_content_manager_can_prepare_draft(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, _product_id, asset_id = _setup(client, normal_user_token_headers)
    manager_email = random_email()
    manager_headers = authentication_token_from_email(
        client=client, email=manager_email, db=db
    )
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/members",
        headers=normal_user_token_headers,
        json={"email": manager_email, "role": "content_manager"},
    )
    draft = _draft(client, manager_headers, brand_id, asset_id)
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/generate-caption",
        headers=manager_headers,
        json={},
    )
    assert response.status_code == 200
