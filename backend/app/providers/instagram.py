import hashlib
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.modules.publishing.models import SocialConnection


class InstagramError(Exception):
    pass


@dataclass(frozen=True)
class PublishResult:
    remote_post_id: str
    remote_post_url: str


def publish_image(
    image_bytes: bytes,
    caption: str,
    connection: SocialConnection,
    image_url: str | None,
) -> PublishResult:
    if settings.INSTAGRAM_PROVIDER == "fake":
        digest = hashlib.sha256(image_bytes + caption.encode()).hexdigest()[:16]
        return PublishResult(
            remote_post_id=f"fake_{digest}",
            remote_post_url=f"https://fake.instagram.local/p/{digest}",
        )

    if not connection.access_token or not connection.external_account_id:
        raise InstagramError("Instagram connection is missing credentials")
    if not image_url:
        raise InstagramError(
            "Real Instagram publishing requires a public or presigned image URL"
        )
    base = settings.INSTAGRAM_GRAPH_BASE.rstrip("/")
    token = connection.access_token
    container = httpx.post(
        f"{base}/{connection.external_account_id}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": token,
        },
        timeout=60,
    )
    if container.status_code >= 400:
        raise InstagramError("Instagram rejected the media container")
    creation_id = container.json().get("id")
    if not creation_id:
        raise InstagramError("Instagram did not return a creation id")
    published = httpx.post(
        f"{base}/{connection.external_account_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
        timeout=60,
    )
    if published.status_code >= 400:
        raise InstagramError("Instagram rejected the publish request")
    remote_id = published.json().get("id")
    if not remote_id:
        raise InstagramError("Instagram did not return a post id")
    return PublishResult(
        remote_post_id=str(remote_id),
        remote_post_url=f"https://www.instagram.com/p/{remote_id}",
    )
