"""Instagram Business tools for reading profiles and recent media via the Graph API.

Uses the Instagram Graph API (for Business/Creator accounts only).
Requires INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID environment variables.

See https://developers.facebook.com/docs/instagram-api/ for API reference.
"""

from __future__ import annotations

import logging
import os

import httpx

from src.humcp.decorator import tool
from src.tools.social.schemas import (
    InstagramMediaData,
    InstagramMediaResponse,
    InstagramProfileData,
    InstagramProfileResponse,
)

logger = logging.getLogger("humcp.tools.instagram")

_GRAPH_BASE = "https://graph.facebook.com/v22.0"


def _get_config() -> tuple[str, str] | None:
    """Return (access_token, account_id) or None if not configured."""
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    if not token or not account_id:
        return None
    return token, account_id


@tool()
async def instagram_get_profile() -> InstagramProfileResponse:
    """Get the Instagram Business account profile information.

    Returns basic profile fields including username, follower count,
    media count, and biography.

    Requires INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID
    environment variables.

    Returns:
        Profile information for the configured Instagram Business account.
    """
    try:
        config = _get_config()
        if config is None:
            return InstagramProfileResponse(
                success=False,
                error="Instagram not configured. Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID environment variables.",
            )

        token, account_id = config
        logger.info("Fetching Instagram profile account_id=%s", account_id)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_GRAPH_BASE}/{account_id}",
                params={
                    "fields": "id,username,name,followers_count,media_count,biography",
                    "access_token": token,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        return InstagramProfileResponse(
            success=True,
            data=InstagramProfileData(
                id=data.get("id"),
                username=data.get("username"),
                name=data.get("name"),
                followers_count=data.get("followers_count"),
                media_count=data.get("media_count"),
                biography=data.get("biography"),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Instagram get_profile HTTP error")
        return InstagramProfileResponse(
            success=False,
            error=f"Instagram API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Instagram get_profile failed")
        return InstagramProfileResponse(
            success=False, error=f"Instagram get_profile failed: {e}"
        )


@tool()
async def instagram_get_recent_media(limit: int = 10) -> InstagramMediaResponse:
    """Get recent media posts from the Instagram Business account.

    Fetches the most recent media (photos, videos, carousels) posted
    by the configured Instagram Business account.

    Args:
        limit: Maximum number of media items to return (1-100, default 10).

    Returns:
        List of recent media items with metadata.
    """
    try:
        config = _get_config()
        if config is None:
            return InstagramMediaResponse(
                success=False,
                error="Instagram not configured. Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID environment variables.",
            )

        token, account_id = config
        capped_limit = max(1, min(limit, 100))
        logger.info(
            "Fetching Instagram recent media account_id=%s limit=%d",
            account_id,
            capped_limit,
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_GRAPH_BASE}/{account_id}/media",
                params={
                    "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
                    "limit": capped_limit,
                    "access_token": token,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        media_items = data.get("data", [])
        logger.info("Instagram recent media fetched count=%d", len(media_items))

        return InstagramMediaResponse(
            success=True,
            data=InstagramMediaData(
                account_id=account_id,
                count=len(media_items),
                media=media_items,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Instagram get_recent_media HTTP error")
        return InstagramMediaResponse(
            success=False,
            error=f"Instagram API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Instagram get_recent_media failed")
        return InstagramMediaResponse(
            success=False, error=f"Instagram get_recent_media failed: {e}"
        )
