from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import UserCreate
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


def _brand_url(brand_id: str) -> str:
    return f"{settings.API_V1_STR}/brands/{brand_id}"


def _create_brand(client: TestClient, headers: dict[str, str], name: str = "Aurum") -> dict:
    response = client.post(
        f"{settings.API_V1_STR}/brands", headers=headers, json={"name": name}
    )
    assert response.status_code == 200, response.text
    return response.json()


def _create_user_and_headers(client: TestClient, db: Session) -> tuple[str, dict[str, str]]:
    email = random_email()
    password = random_lower_string()
    crud.create_user(session=db, user_create=UserCreate(email=email, password=password))
    return email, user_authentication_headers(
        client=client, email=email, password=password
    )


def test_create_brand_and_list(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    brand = _create_brand(client, normal_user_token_headers)
    assert brand["role"] == "owner"
    assert brand["slug"].startswith("aurum-")

    response = client.get(f"{settings.API_V1_STR}/brands", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert any(item["id"] == brand["id"] for item in response.json()["data"])


def test_unrelated_user_cannot_access_brand(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand = _create_brand(client, normal_user_token_headers)
    _, other_headers = _create_user_and_headers(client, db)

    assert client.get(_brand_url(brand["id"]), headers=other_headers).status_code == 404
    assert (
        client.get(f"{_brand_url(brand['id'])}/members", headers=other_headers).status_code
        == 404
    )


def test_superuser_without_membership_is_not_tenant_member(
    client: TestClient, superuser_token_headers: dict[str, str], normal_user_token_headers: dict[str, str]
) -> None:
    brand = _create_brand(client, normal_user_token_headers)
    response = client.get(_brand_url(brand["id"]), headers=superuser_token_headers)
    assert response.status_code == 404


def test_owner_adds_content_manager_and_limits_team_management(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    brand = _create_brand(client, normal_user_token_headers)
    manager_email, manager_headers = _create_user_and_headers(client, db)

    response = client.post(
        f"{_brand_url(brand['id'])}/members",
        headers=normal_user_token_headers,
        json={"email": manager_email, "role": "content_manager"},
    )
    assert response.status_code == 200, response.text
    manager_membership = response.json()
    assert manager_membership["role"] == "content_manager"

    # Manager can read the brand but cannot manage the team.
    assert client.get(_brand_url(brand["id"]), headers=manager_headers).status_code == 200
    forbidden = client.post(
        f"{_brand_url(brand['id'])}/members",
        headers=manager_headers,
        json={"email": random_email(), "role": "owner"},
    )
    assert forbidden.status_code == 403

    # Changing a role is owner-only too.
    assert (
        client.patch(
            f"{_brand_url(brand['id'])}/members/{manager_membership['id']}",
            headers=manager_headers,
            json={"role": "owner"},
        ).status_code
        == 403
    )


def test_brand_must_keep_an_owner(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand = _create_brand(client, normal_user_token_headers)
    members = client.get(
        f"{_brand_url(brand['id'])}/members", headers=normal_user_token_headers
    ).json()["data"]
    owner_membership = members[0]
    response = client.delete(
        f"{_brand_url(brand['id'])}/members/{owner_membership['id']}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400


def test_cannot_add_unknown_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    brand = _create_brand(client, normal_user_token_headers)
    response = client.post(
        f"{_brand_url(brand['id'])}/members",
        headers=normal_user_token_headers,
        json={"email": random_email(), "role": "content_manager"},
    )
    assert response.status_code == 404
