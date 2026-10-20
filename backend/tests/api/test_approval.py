import io
import uuid

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

from app.core.config import settings
from app.modules.generations.models import GeneratedAsset
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def _png(color: tuple[int, int, int] = (160, 125, 80), size: tuple[int, int] = (900, 900)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def _setup(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    brand_id = client.post(
        f"{settings.API_V1_STR}/brands", headers=headers, json={"name": "Approval Brand"}
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
        json={"name": "Signet Ring", "category": "ring"},
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
    return brand_id, generation["assets"][0]["id"]


def _draft_in_review(
    client: TestClient, headers: dict[str, str], brand_id: str, asset_id: str
) -> dict:
    draft = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts",
        headers=headers,
        json={"generated_asset_id": asset_id},
    ).json()
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/generate-caption",
        headers=headers,
        json={},
    )
    submitted = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/submit",
        headers=headers,
    )
    assert submitted.status_code == 200, submitted.text
    return submitted.json()


def test_owner_approval_is_audited(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, asset_id = _setup(client, normal_user_token_headers)
    asset = db.get(GeneratedAsset, uuid.UUID(asset_id))
    assert asset
    asset.integrity_status = "passed"
    db.add(asset)
    db.commit()
    draft = _draft_in_review(client, normal_user_token_headers, brand_id, asset_id)

    approved = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/approve",
        headers=normal_user_token_headers,
    )
    assert approved.status_code == 200, approved.text
    content = approved.json()
    assert content["status"] == "approved"
    assert content["approved_by"]
    assert content["approved_at"]
    me = client.get(
        f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers
    ).json()
    assert content["approved_by"] == me["id"]


def test_content_manager_cannot_approve_or_reject(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, asset_id = _setup(client, normal_user_token_headers)
    draft = _draft_in_review(client, normal_user_token_headers, brand_id, asset_id)
    manager_email = random_email()
    manager_headers = authentication_token_from_email(
        client=client, email=manager_email, db=db
    )
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/members",
        headers=normal_user_token_headers,
        json={"email": manager_email, "role": "content_manager"},
    )
    for action in ("approve", "reject"):
        response = client.post(
            f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/{action}",
            headers=manager_headers,
        )
        assert response.status_code == 403


def test_draft_must_be_submitted_before_approval(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, asset_id = _setup(client, normal_user_token_headers)
    draft = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts",
        headers=normal_user_token_headers,
        json={"generated_asset_id": asset_id},
    ).json()
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/approve",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400


def test_failed_integrity_cannot_be_approved(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    brand_id, _asset_id = _setup(client, normal_user_token_headers)
    product_id = client.get(
        f"{settings.API_V1_STR}/brands/{brand_id}/products",
        headers=normal_user_token_headers,
    ).json()["data"][0]["id"]

    def white_image(*_args, **_kwargs):
        return _png((255, 255, 255), (900, 900))

    monkeypatch.setattr("app.modules.generations.service.generate_image", white_image)
    generation = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/generations",
        headers=normal_user_token_headers,
        json={"product_id": product_id, "mode": "studio"},
    ).json()
    assert generation["assets"][0]["integrity_status"] == "failed"
    draft = _draft_in_review(
        client,
        normal_user_token_headers,
        brand_id,
        generation["assets"][0]["id"],
    )
    response = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/approve",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400


def test_reject_then_edit_and_resubmit(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, asset_id = _setup(client, normal_user_token_headers)
    draft = _draft_in_review(client, normal_user_token_headers, brand_id, asset_id)
    rejected = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/reject",
        headers=normal_user_token_headers,
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"

    edited = client.patch(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}",
        headers=normal_user_token_headers,
        json={"caption": "Revised caption after review."},
    )
    assert edited.status_code == 200
    resubmitted = client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/submit",
        headers=normal_user_token_headers,
    )
    assert resubmitted.status_code == 200
    assert resubmitted.json()["status"] == "needs_approval"


def test_editing_approved_draft_requires_reapproval(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand_id, asset_id = _setup(client, normal_user_token_headers)
    asset = db.get(GeneratedAsset, uuid.UUID(asset_id))
    assert asset
    asset.integrity_status = "passed"
    db.add(asset)
    db.commit()
    draft = _draft_in_review(client, normal_user_token_headers, brand_id, asset_id)
    client.post(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}/approve",
        headers=normal_user_token_headers,
    )
    edited = client.patch(
        f"{settings.API_V1_STR}/brands/{brand_id}/drafts/{draft['id']}",
        headers=normal_user_token_headers,
        json={"caption": "Changed after approval."},
    )
    assert edited.status_code == 200
    assert edited.json()["status"] == "needs_approval"
    assert edited.json()["approved_by"] is None
