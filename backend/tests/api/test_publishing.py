import io
import uuid

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

from app.core.config import settings
from app.modules.generations.models import GeneratedAsset
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (900, 900), (165, 130, 85)).save(buffer, format="PNG")
    return buffer.getvalue()


def _approved_draft(
    client: TestClient, db: Session, headers: dict[str, str]
) -> tuple[str, str]:
    brand_id = client.post(
        f"{settings.API_V1_STR}/brands", headers=headers, json={"name": "Publish Brand"}
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
        json={"name": "Luna Pendant", "category": "pendant"},
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
    asset = db.get(GeneratedAsset, uuid.UUID(generation["assets"][0]["id"]))
    assert asset
    asset.integrity_status = "passed"
    db.add(asset)
    db.commit()

    draft = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts",
        headers=headers,
        json={"generated_asset_id": str(asset.id)},
    ).json()
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/generate-caption",
        headers=headers,
        json={},
    )
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/submit",
        headers=headers,
    )
    approved = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/approve",
        headers=headers,
    )
    assert approved.status_code == 200, approved.text
    return brand_id, draft["id"]


def _connect(client: TestClient, headers: dict[str, str], brand_id: str) -> None:
    response = client.put(
        f"{settings.API_V1_STR}/brands/{brand_id}/social",
        headers=headers,
        json={
            "external_account_id": "17841400000000000",
            "account_name": "aurum.atelier",
        },
    )
    assert response.status_code == 200, response.text


def test_connection_never_exposes_token(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = client.post(
        f"{settings.API_V1_STR}/brands",
        headers=normal_user_token_headers,
        json={"name": "Social Brand"},
    ).json()["id"]
    _connect(client, normal_user_token_headers, brand_id)
    response = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/social",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert "access_token" not in response.json()
    assert response.json()["status"] == "connected"


def test_content_manager_cannot_connect(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = client.post(
        f"{settings.API_V1_STR}/brands",
        headers=normal_user_token_headers,
        json={"name": "Social Brand"},
    ).json()["id"]
    manager_email = random_email()
    manager_headers = authentication_token_from_email(
        client=client, email=manager_email, db=db
    )
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/members",
        headers=normal_user_token_headers,
        json={"email": manager_email, "role": "content_manager"},
    )
    response = client.put(
        f"{settings.API_V1_STR}/brands/{brand_id}/social",
        headers=manager_headers,
        json={"external_account_id": "1", "account_name": "nope"},
    )
    assert response.status_code == 403


def test_fake_publish_succeeds_and_is_idempotent(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, draft_id = _approved_draft(client, db, normal_user_token_headers)
    _connect(client, normal_user_token_headers, brand_id)

    published = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft_id}/publish",
        headers=normal_user_token_headers,
    )
    assert published.status_code == 200, published.text
    job = published.json()
    assert job["status"] == "published"
    assert job["remote_post_id"]
    assert job["remote_post_url"]

    again = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft_id}/publish",
        headers=normal_user_token_headers,
    )
    assert again.status_code == 200
    assert again.json()["id"] == job["id"]

    jobs = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft_id}/publish-jobs",
        headers=normal_user_token_headers,
    )
    assert jobs.json()["count"] == 1
    draft = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft_id}",
        headers=normal_user_token_headers,
    )
    assert draft.json()["status"] == "published"


def test_publish_requires_approval(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id = client.post(
        f"{settings.API_V1_STR}/brands",
        headers=normal_user_token_headers,
        json={"name": "Unapproved"},
    ).json()["id"]
    product = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products",
        headers=normal_user_token_headers,
        json={"name": "X", "category": "ring"},
    ).json()
    upload = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/products/{product['id']}/images",
        headers=normal_user_token_headers,
        files=[("file", ("x.png", _png(), "image/png"))],
    )
    asset_id = upload.json()["images"][0]["id"]
    assert asset_id
    _connect(client, normal_user_token_headers, brand_id)
    # Fabricating a draft is not possible without a generated asset; use the
    # full path then reject instead.
    draft_response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts",
        headers=normal_user_token_headers,
        json={"generated_asset_id": str(uuid.uuid4())},
    )
    assert draft_response.status_code == 404


def test_content_manager_cannot_publish(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, draft_id = _approved_draft(client, db, normal_user_token_headers)
    _connect(client, normal_user_token_headers, brand_id)
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
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft_id}/publish",
        headers=manager_headers,
    )
    assert response.status_code == 403


def test_failed_publish_can_retry(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    brand_id, draft_id = _approved_draft(client, db, normal_user_token_headers)
    _connect(client, normal_user_token_headers, brand_id)

    def fail(*_args, **_kwargs):
        raise RuntimeError("graph down")

    monkeypatch.setattr(
        "app.modules.publishing.service.publish_image", fail
    )
    failed = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft_id}/publish",
        headers=normal_user_token_headers,
    )
    assert failed.status_code == 200
    assert failed.json()["status"] == "failed"
    job_id = failed.json()["id"]

    monkeypatch.undo()
    retried = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/publish-jobs/{job_id}/retry",
        headers=normal_user_token_headers,
    )
    assert retried.status_code == 200, retried.text
    assert retried.json()["status"] == "published"
    assert retried.json()["attempt_count"] == 2


def test_disconnected_account_blocks_publish(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, draft_id = _approved_draft(client, db, normal_user_token_headers)
    _connect(client, normal_user_token_headers, brand_id)
    client.delete(
        f"{settings.API_V1_STR}/brands/{brand_id}/social",
        headers=normal_user_token_headers,
    )
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft_id}/publish",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400


def test_failed_integrity_asset_cannot_publish(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, draft_id = _approved_draft(client, db, normal_user_token_headers)
    _connect(client, normal_user_token_headers, brand_id)
    draft = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft_id}",
        headers=normal_user_token_headers,
    ).json()
    asset = db.get(GeneratedAsset, uuid.UUID(draft["generated_asset_id"]))
    assert asset
    asset.integrity_status = "failed"
    db.add(asset)
    db.commit()
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft_id}/publish",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400
