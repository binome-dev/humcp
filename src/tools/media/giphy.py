"""Giphy tools for searching and retrieving GIFs."""

from __future__ import annotations

import logging

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.media.schemas import (
    GiphyGif,
    GiphyRandomData,
    GiphyRandomResponse,
    GiphySearchData,
    GiphySearchResponse,
    GiphyTrendingData,
    GiphyTrendingResponse,
)

logger = logging.getLogger("humcp.tools.giphy")

GIPHY_API_BASE = "https://api.giphy.com/v1/gifs"


def _parse_gif(gif: dict) -> GiphyGif:
    """Extract relevant fields from a Giphy API gif object."""
    images = gif.get("images", {})
    original = images.get("original", {})
    return GiphyGif(
        url=original.get("url", ""),
        alt_text=gif.get("alt_text"),
        title=gif.get("title"),
    )


@tool()
async def giphy_search(
    query: str,
    limit: int = 5,
    rating: str = "g",
) -> GiphySearchResponse:
    """Search for GIFs on Giphy by keyword.

    Args:
        query: The search query string (e.g., "happy dance", "thumbs up").
        limit: Maximum number of GIFs to return (1-50). Default: 5.
        rating: Content rating filter. One of "g", "pg", "pg-13", "r". Default: "g".

    Returns:
        Search results with GIF URLs and metadata.
    """
    try:
        api_key = await resolve_credential("GIPHY_API_KEY")
        if not api_key:
            return GiphySearchResponse(
                success=False,
                error="Giphy API not configured. Set GIPHY_API_KEY environment variable.",
            )

        if not query.strip():
            return GiphySearchResponse(success=False, error="Query must not be empty.")

        clamped_limit = max(1, min(limit, 50))
        valid_ratings = {"g", "pg", "pg-13", "r"}
        resolved_rating = rating if rating in valid_ratings else "g"

        params = {
            "api_key": api_key,
            "q": query,
            "limit": clamped_limit,
            "rating": resolved_rating,
        }

        logger.info(
            "Giphy search query=%s limit=%d rating=%s",
            query,
            clamped_limit,
            resolved_rating,
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{GIPHY_API_BASE}/search", params=params)
            response.raise_for_status()

        data = response.json()
        gifs = [_parse_gif(gif) for gif in data.get("data", [])]
        total_count = data.get("pagination", {}).get("total_count", 0)

        logger.info("Giphy search complete results=%d total=%d", len(gifs), total_count)

        return GiphySearchResponse(
            success=True,
            data=GiphySearchData(
                query=query,
                gifs=gifs,
                total_count=total_count,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Giphy search HTTP error status=%d", e.response.status_code)
        return GiphySearchResponse(
            success=False, error=f"Giphy API error: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("Giphy search failed")
        return GiphySearchResponse(
            success=False, error=f"Giphy search failed: {str(e)}"
        )


@tool()
async def giphy_trending(
    limit: int = 10,
) -> GiphyTrendingResponse:
    """Get trending GIFs from Giphy.

    Args:
        limit: Maximum number of trending GIFs to return (1-50). Default: 10.

    Returns:
        List of currently trending GIFs.
    """
    try:
        api_key = await resolve_credential("GIPHY_API_KEY")
        if not api_key:
            return GiphyTrendingResponse(
                success=False,
                error="Giphy API not configured. Set GIPHY_API_KEY environment variable.",
            )

        clamped_limit = max(1, min(limit, 50))

        params = {
            "api_key": api_key,
            "limit": clamped_limit,
        }

        logger.info("Giphy trending limit=%d", clamped_limit)

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{GIPHY_API_BASE}/trending", params=params)
            response.raise_for_status()

        data = response.json()
        gifs = [_parse_gif(gif) for gif in data.get("data", [])]

        logger.info("Giphy trending complete results=%d", len(gifs))

        return GiphyTrendingResponse(
            success=True,
            data=GiphyTrendingData(gifs=gifs),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Giphy trending HTTP error status=%d", e.response.status_code)
        return GiphyTrendingResponse(
            success=False, error=f"Giphy API error: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("Giphy trending failed")
        return GiphyTrendingResponse(
            success=False, error=f"Giphy trending failed: {str(e)}"
        )


@tool()
async def giphy_random(
    tag: str | None = None,
    rating: str = "g",
) -> GiphyRandomResponse:
    """Get a random GIF from Giphy, optionally filtered by tag.

    Args:
        tag: Optional tag to filter the random GIF (e.g., "cats", "funny").
        rating: Content rating filter. One of "g", "pg", "pg-13", "r". Default: "g".

    Returns:
        A single random GIF with URL and metadata.
    """
    try:
        api_key = await resolve_credential("GIPHY_API_KEY")
        if not api_key:
            return GiphyRandomResponse(
                success=False,
                error="Giphy API not configured. Set GIPHY_API_KEY environment variable.",
            )

        valid_ratings = {"g", "pg", "pg-13", "r"}
        resolved_rating = rating if rating in valid_ratings else "g"

        params: dict = {
            "api_key": api_key,
            "rating": resolved_rating,
        }

        if tag and tag.strip():
            params["tag"] = tag.strip()

        logger.info("Giphy random tag=%s rating=%s", tag, resolved_rating)

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{GIPHY_API_BASE}/random", params=params)
            response.raise_for_status()

        data = response.json()
        gif_data = data.get("data", {})

        if not gif_data:
            return GiphyRandomResponse(success=False, error="No random GIF returned.")

        gif = _parse_gif(gif_data)

        logger.info("Giphy random complete title=%s", gif.title)

        return GiphyRandomResponse(
            success=True,
            data=GiphyRandomData(
                tag=tag,
                gif=gif,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Giphy random HTTP error status=%d", e.response.status_code)
        return GiphyRandomResponse(
            success=False, error=f"Giphy API error: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("Giphy random failed")
        return GiphyRandomResponse(
            success=False, error=f"Giphy random failed: {str(e)}"
        )
