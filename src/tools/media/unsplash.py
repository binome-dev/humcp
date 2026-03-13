"""Unsplash tools for searching and retrieving high-quality royalty-free photos."""

from __future__ import annotations

import logging

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.media.schemas import (
    UnsplashGetPhotoData,
    UnsplashGetPhotoResponse,
    UnsplashPhoto,
    UnsplashRandomPhotoData,
    UnsplashRandomPhotoResponse,
    UnsplashSearchData,
    UnsplashSearchResponse,
)

logger = logging.getLogger("humcp.tools.unsplash")

UNSPLASH_API_BASE = "https://api.unsplash.com"


def _format_photo(photo: dict) -> UnsplashPhoto:
    """Extract relevant fields from an Unsplash API photo object."""
    urls = photo.get("urls", {})
    user = photo.get("user", {})
    return UnsplashPhoto(
        id=photo.get("id", ""),
        description=photo.get("description") or photo.get("alt_description"),
        width=photo.get("width"),
        height=photo.get("height"),
        color=photo.get("color"),
        urls={
            "raw": urls.get("raw"),
            "full": urls.get("full"),
            "regular": urls.get("regular"),
            "small": urls.get("small"),
            "thumb": urls.get("thumb"),
        },
        author_name=user.get("name"),
        author_username=user.get("username"),
        likes=photo.get("likes"),
    )


@tool()
async def unsplash_search_photos(
    query: str,
    per_page: int = 10,
    page: int = 1,
    orientation: str | None = None,
    color: str | None = None,
) -> UnsplashSearchResponse:
    """Search for photos on Unsplash by keyword.

    Args:
        query: The search query string (e.g., "mountain sunset", "office workspace").
        per_page: Number of results per page (1-30). Default: 10.
        page: Page number to retrieve. Default: 1.
        orientation: Filter by orientation: "landscape", "portrait", or "squarish".
        color: Filter by color: "black_and_white", "black", "white", "yellow",
            "orange", "red", "purple", "magenta", "green", "teal", "blue".

    Returns:
        Search results with photo URLs, author info, and metadata.
    """
    try:
        access_key = await resolve_credential("UNSPLASH_ACCESS_KEY")
        if not access_key:
            return UnsplashSearchResponse(
                success=False,
                error="Unsplash API not configured. Set UNSPLASH_ACCESS_KEY environment variable.",
            )

        if not query.strip():
            return UnsplashSearchResponse(
                success=False, error="Query must not be empty."
            )

        params: dict = {
            "query": query,
            "per_page": max(1, min(per_page, 30)),
            "page": max(1, page),
        }

        valid_orientations = {"landscape", "portrait", "squarish"}
        if orientation and orientation in valid_orientations:
            params["orientation"] = orientation

        valid_colors = {
            "black_and_white",
            "black",
            "white",
            "yellow",
            "orange",
            "red",
            "purple",
            "magenta",
            "green",
            "teal",
            "blue",
        }
        if color and color in valid_colors:
            params["color"] = color

        headers = {
            "Authorization": f"Client-ID {access_key}",
            "Accept-Version": "v1",
        }

        logger.info("Unsplash search query=%s per_page=%d", query, params["per_page"])

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{UNSPLASH_API_BASE}/search/photos",
                params=params,
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()
        photos = [_format_photo(photo) for photo in data.get("results", [])]
        total = data.get("total", 0)

        logger.info("Unsplash search complete results=%d total=%d", len(photos), total)

        return UnsplashSearchResponse(
            success=True,
            data=UnsplashSearchData(
                query=query,
                total=total,
                photos=photos,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Unsplash search HTTP error status=%d", e.response.status_code)
        return UnsplashSearchResponse(
            success=False, error=f"Unsplash API error: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("Unsplash search failed")
        return UnsplashSearchResponse(
            success=False, error=f"Unsplash search failed: {str(e)}"
        )


@tool()
async def unsplash_get_random_photo(
    query: str | None = None,
    orientation: str | None = None,
    count: int = 1,
) -> UnsplashRandomPhotoResponse:
    """Get random photo(s) from Unsplash, optionally filtered by query.

    Args:
        query: Optional search query to filter random photos.
        orientation: Filter by orientation: "landscape", "portrait", or "squarish".
        count: Number of random photos to return (1-30). Default: 1.

    Returns:
        Random photo(s) with URLs and metadata.
    """
    try:
        access_key = await resolve_credential("UNSPLASH_ACCESS_KEY")
        if not access_key:
            return UnsplashRandomPhotoResponse(
                success=False,
                error="Unsplash API not configured. Set UNSPLASH_ACCESS_KEY environment variable.",
            )

        params: dict = {
            "count": max(1, min(count, 30)),
        }

        if query:
            params["query"] = query

        valid_orientations = {"landscape", "portrait", "squarish"}
        if orientation and orientation in valid_orientations:
            params["orientation"] = orientation

        headers = {
            "Authorization": f"Client-ID {access_key}",
            "Accept-Version": "v1",
        }

        logger.info("Unsplash random query=%s count=%d", query, params["count"])

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{UNSPLASH_API_BASE}/photos/random",
                params=params,
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()

        if isinstance(data, list):
            photos = [_format_photo(photo) for photo in data]
        else:
            photos = [_format_photo(data)]

        logger.info("Unsplash random complete results=%d", len(photos))

        return UnsplashRandomPhotoResponse(
            success=True,
            data=UnsplashRandomPhotoData(
                query=query,
                photos=photos,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Unsplash random HTTP error status=%d", e.response.status_code)
        return UnsplashRandomPhotoResponse(
            success=False, error=f"Unsplash API error: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("Unsplash random photo failed")
        return UnsplashRandomPhotoResponse(
            success=False, error=f"Unsplash random photo failed: {str(e)}"
        )


@tool()
async def unsplash_get_photo(
    photo_id: str,
) -> UnsplashGetPhotoResponse:
    """Get a specific photo from Unsplash by its ID.

    Args:
        photo_id: The unique identifier of the Unsplash photo.

    Returns:
        Photo details including URLs, author info, and metadata.
    """
    try:
        access_key = await resolve_credential("UNSPLASH_ACCESS_KEY")
        if not access_key:
            return UnsplashGetPhotoResponse(
                success=False,
                error="Unsplash API not configured. Set UNSPLASH_ACCESS_KEY environment variable.",
            )

        if not photo_id.strip():
            return UnsplashGetPhotoResponse(
                success=False, error="Photo ID must not be empty."
            )

        headers = {
            "Authorization": f"Client-ID {access_key}",
            "Accept-Version": "v1",
        }

        logger.info("Unsplash get photo id=%s", photo_id)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{UNSPLASH_API_BASE}/photos/{photo_id}",
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()
        photo = _format_photo(data)

        logger.info("Unsplash get photo complete id=%s", photo_id)

        return UnsplashGetPhotoResponse(
            success=True,
            data=UnsplashGetPhotoData(photo=photo),
        )
    except httpx.HTTPStatusError as e:
        logger.exception(
            "Unsplash get photo HTTP error status=%d", e.response.status_code
        )
        return UnsplashGetPhotoResponse(
            success=False, error=f"Unsplash API error: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("Unsplash get photo failed")
        return UnsplashGetPhotoResponse(
            success=False, error=f"Unsplash get photo failed: {str(e)}"
        )
