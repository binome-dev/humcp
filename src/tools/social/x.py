"""X (Twitter) tools for posting tweets, searching, and fetching user info via API v2."""

from __future__ import annotations

import logging
import os

import httpx

from src.humcp.decorator import tool
from src.tools.social.schemas import (
    XMentionsData,
    XMentionsResponse,
    XPostTweetData,
    XPostTweetResponse,
    XReplyTweetData,
    XReplyTweetResponse,
    XSearchTweetsData,
    XSearchTweetsResponse,
    XTweet,
    XTweetPublicMetrics,
    XUserData,
    XUserResponse,
    XUserTweetsData,
    XUserTweetsResponse,
)

logger = logging.getLogger("humcp.tools.x")

_BASE_URL = "https://api.twitter.com/2"


def _get_bearer_headers() -> dict[str, str] | None:
    """Return Authorization headers using the bearer token, or None if not configured."""
    token = os.getenv("X_BEARER_TOKEN")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


def _get_oauth_headers(method: str, url: str) -> dict[str, str] | None:
    """Return OAuth 1.0a headers for write operations.

    Requires X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, and X_ACCESS_TOKEN_SECRET.
    Uses the authlib library for OAuth1 signing.
    """
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_token_secret]):
        return None

    try:
        from authlib.integrations.httpx_client import OAuth1Auth  # type: ignore

        auth = OAuth1Auth(
            client_id=api_key,
            client_secret=api_secret,
            token=access_token,
            token_secret=access_token_secret,
        )
        # Build a dummy request to sign
        req = httpx.Request(method, url)
        signed = auth(req)
        return dict(signed.headers)
    except ImportError:
        logger.warning(
            "authlib is required for OAuth1 signing. Install with: pip install authlib"
        )
        return None


@tool()
async def x_post_tweet(text: str) -> XPostTweetResponse:
    """Post a new tweet on X (Twitter).

    Args:
        text: The text content of the tweet (max 280 characters).

    Returns:
        The created tweet details or an error message.
    """
    try:
        url = f"{_BASE_URL}/tweets"
        headers = _get_oauth_headers("POST", url)
        if headers is None:
            return XPostTweetResponse(
                success=False,
                error="X API not configured for posting. Set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, and X_ACCESS_TOKEN_SECRET.",
            )

        if len(text) > 280:
            return XPostTweetResponse(
                success=False,
                error=f"Tweet text exceeds 280 characters (got {len(text)}).",
            )

        logger.info("X post tweet length=%d", len(text))
        headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json={"text": text},
            )
            response.raise_for_status()
            data = response.json()

        tweet_id = data["data"]["id"]
        tweet_text = data["data"]["text"]
        tweet_url = f"https://x.com/i/status/{tweet_id}"

        logger.info("X tweet posted id=%s", tweet_id)
        return XPostTweetResponse(
            success=True,
            data=XPostTweetData(
                id=tweet_id,
                text=tweet_text,
                url=tweet_url,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("X post tweet HTTP error")
        return XPostTweetResponse(
            success=False,
            error=f"X API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("X post tweet failed")
        return XPostTweetResponse(success=False, error=f"X post tweet failed: {e}")


def _parse_tweet(tweet_data: dict, users_map: dict[str, str]) -> XTweet:
    """Parse a single tweet response dict into an XTweet model."""
    author_id = tweet_data.get("author_id")
    username = users_map.get(author_id, "unknown") if author_id else "unknown"

    metrics = tweet_data.get("public_metrics")
    public_metrics = None
    if metrics:
        public_metrics = XTweetPublicMetrics(
            retweet_count=metrics.get("retweet_count", 0),
            reply_count=metrics.get("reply_count", 0),
            like_count=metrics.get("like_count", 0),
            quote_count=metrics.get("quote_count", 0),
            bookmark_count=metrics.get("bookmark_count", 0),
            impression_count=metrics.get("impression_count", 0),
        )

    return XTweet(
        id=tweet_data["id"],
        text=tweet_data["text"],
        author_id=author_id,
        author_username=username,
        created_at=tweet_data.get("created_at"),
        url=f"https://x.com/{username}/status/{tweet_data['id']}",
        public_metrics=public_metrics,
    )


@tool()
async def x_search_tweets(
    query: str,
    max_results: int = 10,
) -> XSearchTweetsResponse:
    """Search recent tweets on X (Twitter) matching a query.

    Uses the Twitter API v2 recent search endpoint. Returns tweets from the
    last 7 days matching the query, including public engagement metrics.

    Args:
        query: The search query string. Supports Twitter search operators (e.g. "from:user", "#hashtag", "lang:en").
        max_results: Maximum number of results to return (10-100, default 10).

    Returns:
        Matching tweets with public metrics or an error message.
    """
    try:
        headers = _get_bearer_headers()
        if headers is None:
            return XSearchTweetsResponse(
                success=False,
                error="X API not configured. Set X_BEARER_TOKEN environment variable.",
            )

        max_results = max(10, min(max_results, 100))
        logger.info("X search query=%r max_results=%d", query, max_results)

        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "author_id,created_at,text,public_metrics",
            "expansions": "author_id",
            "user.fields": "username",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_BASE_URL}/tweets/search/recent",
                headers=headers,
                params=params,  # type: ignore[arg-type]
            )
            response.raise_for_status()
            data = response.json()

        # Build user lookup
        users_map: dict[str, str] = {}
        for user in data.get("includes", {}).get("users", []):
            users_map[user["id"]] = user.get("username", "unknown")

        tweets: list[XTweet] = [
            _parse_tweet(td, users_map) for td in data.get("data", [])
        ]

        logger.info("X search complete results=%d", len(tweets))
        return XSearchTweetsResponse(
            success=True,
            data=XSearchTweetsData(
                query=query,
                count=len(tweets),
                tweets=tweets,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("X search tweets HTTP error")
        return XSearchTweetsResponse(
            success=False,
            error=f"X API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("X search tweets failed")
        return XSearchTweetsResponse(
            success=False, error=f"X search tweets failed: {e}"
        )


@tool()
async def x_get_user(username: str) -> XUserResponse:
    """Get public profile information for an X (Twitter) user.

    Returns the user's profile details including bio, location, profile image,
    account creation date, verification status, and public metrics.

    Args:
        username: The X username / handle (without the @ symbol).

    Returns:
        User profile details or an error message.
    """
    try:
        headers = _get_bearer_headers()
        if headers is None:
            return XUserResponse(
                success=False,
                error="X API not configured. Set X_BEARER_TOKEN environment variable.",
            )

        logger.info("X get user username=%s", username)

        params = {
            "user.fields": "created_at,description,location,profile_image_url,public_metrics,url,verified",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_BASE_URL}/users/by/username/{username}",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        user_data = data.get("data")
        if not user_data:
            return XUserResponse(
                success=False,
                error=f"User '{username}' not found.",
            )

        metrics = user_data.get("public_metrics", {})
        return XUserResponse(
            success=True,
            data=XUserData(
                id=user_data["id"],
                name=user_data["name"],
                username=user_data["username"],
                description=user_data.get("description"),
                profile_image_url=user_data.get("profile_image_url"),
                location=user_data.get("location"),
                url=user_data.get("url"),
                created_at=user_data.get("created_at"),
                verified=user_data.get("verified", False),
                followers_count=metrics.get("followers_count", 0),
                following_count=metrics.get("following_count", 0),
                tweet_count=metrics.get("tweet_count", 0),
                listed_count=metrics.get("listed_count", 0),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("X get user HTTP error")
        return XUserResponse(
            success=False,
            error=f"X API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("X get user failed")
        return XUserResponse(success=False, error=f"X get user failed: {e}")


@tool()
async def x_get_user_tweets(
    username: str,
    max_results: int = 10,
) -> XUserTweetsResponse:
    """Get recent tweets posted by a specific X (Twitter) user.

    First resolves the username to a user ID, then fetches their recent tweets
    including public engagement metrics (likes, retweets, replies, etc.).

    Args:
        username: The X username / handle (without the @ symbol).
        max_results: Maximum number of tweets to return (5-100, default 10).

    Returns:
        List of the user's recent tweets or an error message.
    """
    try:
        headers = _get_bearer_headers()
        if headers is None:
            return XUserTweetsResponse(
                success=False,
                error="X API not configured. Set X_BEARER_TOKEN environment variable.",
            )

        max_results = max(5, min(max_results, 100))
        logger.info(
            "X get user tweets username=%s max_results=%d", username, max_results
        )

        async with httpx.AsyncClient() as client:
            # First resolve username to user ID
            user_resp = await client.get(
                f"{_BASE_URL}/users/by/username/{username}",
                headers=headers,
                params={"user.fields": "id"},
            )
            user_resp.raise_for_status()
            user_json = user_resp.json()

        user_data = user_json.get("data")
        if not user_data:
            return XUserTweetsResponse(
                success=False,
                error=f"User '{username}' not found.",
            )

        user_id = user_data["id"]

        async with httpx.AsyncClient() as client:
            tweets_resp = await client.get(
                f"{_BASE_URL}/users/{user_id}/tweets",
                headers=headers,
                params={
                    "max_results": max_results,
                    "tweet.fields": "author_id,created_at,text,public_metrics",
                    "expansions": "author_id",
                    "user.fields": "username",
                },
            )
            tweets_resp.raise_for_status()
            data = tweets_resp.json()

        users_map: dict[str, str] = {}
        for user in data.get("includes", {}).get("users", []):
            users_map[user["id"]] = user.get("username", "unknown")

        tweets: list[XTweet] = [
            _parse_tweet(td, users_map) for td in data.get("data", [])
        ]

        logger.info("X get user tweets complete results=%d", len(tweets))
        return XUserTweetsResponse(
            success=True,
            data=XUserTweetsData(
                user_id=user_id,
                username=username,
                count=len(tweets),
                tweets=tweets,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("X get user tweets HTTP error")
        return XUserTweetsResponse(
            success=False,
            error=f"X API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("X get user tweets failed")
        return XUserTweetsResponse(
            success=False, error=f"X get user tweets failed: {e}"
        )


@tool()
async def x_reply_to_tweet(tweet_id: str, text: str) -> XReplyTweetResponse:
    """Reply to an existing tweet on X (Twitter).

    Posts a new tweet as a reply to the specified tweet. Requires OAuth 1.0a
    credentials (same as posting a tweet).

    Args:
        tweet_id: The ID of the tweet to reply to.
        text: The text content of the reply (max 280 characters).

    Returns:
        The created reply tweet details or an error message.
    """
    try:
        url = f"{_BASE_URL}/tweets"
        headers = _get_oauth_headers("POST", url)
        if headers is None:
            return XReplyTweetResponse(
                success=False,
                error="X API not configured for posting. Set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, and X_ACCESS_TOKEN_SECRET.",
            )

        if len(text) > 280:
            return XReplyTweetResponse(
                success=False,
                error=f"Reply text exceeds 280 characters (got {len(text)}).",
            )

        logger.info("X reply to tweet_id=%s length=%d", tweet_id, len(text))
        headers["Content-Type"] = "application/json"

        payload = {
            "text": text,
            "reply": {"in_reply_to_tweet_id": tweet_id},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        reply_id = data["data"]["id"]
        reply_text = data["data"]["text"]
        reply_url = f"https://x.com/i/status/{reply_id}"

        logger.info("X reply posted id=%s in_reply_to=%s", reply_id, tweet_id)
        return XReplyTweetResponse(
            success=True,
            data=XReplyTweetData(
                id=reply_id,
                text=reply_text,
                in_reply_to_tweet_id=tweet_id,
                url=reply_url,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("X reply to tweet HTTP error")
        return XReplyTweetResponse(
            success=False,
            error=f"X API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("X reply to tweet failed")
        return XReplyTweetResponse(success=False, error=f"X reply to tweet failed: {e}")


@tool()
async def x_get_mentions(
    username: str,
    max_results: int = 10,
) -> XMentionsResponse:
    """Get recent tweets mentioning a specific X (Twitter) user.

    First resolves the username to a user ID, then fetches recent mentions
    using the Twitter API v2 user mentions timeline endpoint.

    Args:
        username: The X username / handle (without the @ symbol).
        max_results: Maximum number of mentions to return (5-100, default 10).

    Returns:
        List of tweets mentioning the user or an error message.
    """
    try:
        headers = _get_bearer_headers()
        if headers is None:
            return XMentionsResponse(
                success=False,
                error="X API not configured. Set X_BEARER_TOKEN environment variable.",
            )

        max_results = max(5, min(max_results, 100))
        logger.info("X get mentions username=%s max_results=%d", username, max_results)

        async with httpx.AsyncClient() as client:
            # Resolve username to user ID
            user_resp = await client.get(
                f"{_BASE_URL}/users/by/username/{username}",
                headers=headers,
                params={"user.fields": "id"},
            )
            user_resp.raise_for_status()
            user_json = user_resp.json()

        user_data = user_json.get("data")
        if not user_data:
            return XMentionsResponse(
                success=False,
                error=f"User '{username}' not found.",
            )

        user_id = user_data["id"]

        async with httpx.AsyncClient() as client:
            mentions_resp = await client.get(
                f"{_BASE_URL}/users/{user_id}/mentions",
                headers=headers,
                params={
                    "max_results": max_results,
                    "tweet.fields": "author_id,created_at,text,public_metrics",
                    "expansions": "author_id",
                    "user.fields": "username",
                },
            )
            mentions_resp.raise_for_status()
            data = mentions_resp.json()

        users_map: dict[str, str] = {}
        for user in data.get("includes", {}).get("users", []):
            users_map[user["id"]] = user.get("username", "unknown")

        tweets: list[XTweet] = [
            _parse_tweet(td, users_map) for td in data.get("data", [])
        ]

        logger.info("X get mentions complete results=%d", len(tweets))
        return XMentionsResponse(
            success=True,
            data=XMentionsData(
                user_id=user_id,
                count=len(tweets),
                tweets=tweets,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("X get mentions HTTP error")
        return XMentionsResponse(
            success=False,
            error=f"X API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("X get mentions failed")
        return XMentionsResponse(success=False, error=f"X get mentions failed: {e}")
