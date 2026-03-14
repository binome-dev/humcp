"""LinkedIn tools for reading profiles and creating posts via the LinkedIn API.

Uses the LinkedIn Marketing/Community Management API v2.
Requires LINKEDIN_ACCESS_TOKEN environment variable (OAuth 2.0 token with
appropriate scopes: r_liteprofile, w_member_social).

See https://learn.microsoft.com/en-us/linkedin/marketing/ for API reference.
"""

from __future__ import annotations

import logging
import os

import httpx

from src.humcp.decorator import tool
from src.tools.social.schemas import (
    LinkedInProfileData,
    LinkedInProfileResponse,
    LinkedInShareData,
    LinkedInShareResponse,
)

logger = logging.getLogger("humcp.tools.linkedin")

_BASE_URL = "https://api.linkedin.com/v2"


def _get_headers() -> dict[str, str] | None:
    """Return Authorization headers using the LinkedIn access token."""
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


@tool()
async def linkedin_get_profile() -> LinkedInProfileResponse:
    """Get the authenticated LinkedIn user's profile information.

    Returns basic profile fields including name, headline, and vanity name.
    Requires a valid LinkedIn OAuth 2.0 access token with the r_liteprofile scope.

    Returns:
        Profile information for the authenticated user, or an error.
    """
    try:
        headers = _get_headers()
        if headers is None:
            return LinkedInProfileResponse(
                success=False,
                error="LinkedIn not configured. Set LINKEDIN_ACCESS_TOKEN environment variable.",
            )

        logger.info("Fetching LinkedIn profile")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_BASE_URL}/me",
                headers=headers,
                params={
                    "projection": "(id,firstName,lastName,vanityName,localizedHeadline)"
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        first_name = None
        fn = data.get("firstName", {}).get("localized", {})
        if fn:
            first_name = next(iter(fn.values()), None)

        last_name = None
        ln = data.get("lastName", {}).get("localized", {})
        if ln:
            last_name = next(iter(ln.values()), None)

        return LinkedInProfileResponse(
            success=True,
            data=LinkedInProfileData(
                urn=f"urn:li:person:{data.get('id', '')}",
                first_name=first_name,
                last_name=last_name,
                headline=data.get("localizedHeadline"),
                vanity_name=data.get("vanityName"),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("LinkedIn get_profile HTTP error")
        return LinkedInProfileResponse(
            success=False,
            error=f"LinkedIn API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("LinkedIn get_profile failed")
        return LinkedInProfileResponse(
            success=False, error=f"LinkedIn get_profile failed: {e}"
        )


@tool()
async def linkedin_create_share(text: str) -> LinkedInShareResponse:
    """Create a text post (share) on LinkedIn as the authenticated user.

    Posts a new share to the authenticated user's LinkedIn feed. Requires
    a valid LinkedIn OAuth 2.0 access token with the w_member_social scope.

    Args:
        text: The text content of the post (up to 3000 characters).

    Returns:
        The created share ID and URL, or an error.
    """
    try:
        headers = _get_headers()
        if headers is None:
            return LinkedInShareResponse(
                success=False,
                error="LinkedIn not configured. Set LINKEDIN_ACCESS_TOKEN environment variable.",
            )

        if len(text) > 3000:
            return LinkedInShareResponse(
                success=False,
                error=f"Post text exceeds 3000 characters (got {len(text)}).",
            )

        # First get the authenticated user's URN
        async with httpx.AsyncClient() as client:
            me_resp = await client.get(
                f"{_BASE_URL}/me",
                headers=headers,
                timeout=30,
            )
            me_resp.raise_for_status()
            me_data = me_resp.json()

        author_urn = f"urn:li:person:{me_data['id']}"

        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        logger.info("Creating LinkedIn share length=%d", len(text))
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{_BASE_URL}/ugcPosts",
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        share_id = data.get("id", "")
        logger.info("LinkedIn share created id=%s", share_id)

        return LinkedInShareResponse(
            success=True,
            data=LinkedInShareData(
                share_id=share_id,
                url=f"https://www.linkedin.com/feed/update/{share_id}/" if share_id else None,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("LinkedIn create_share HTTP error")
        return LinkedInShareResponse(
            success=False,
            error=f"LinkedIn API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("LinkedIn create_share failed")
        return LinkedInShareResponse(
            success=False, error=f"LinkedIn create_share failed: {e}"
        )
