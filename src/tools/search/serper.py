from __future__ import annotations

import logging

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.search.schemas import (
    SearchResult,
    SerperImageResult,
    SerperImagesData,
    SerperImagesResponse,
    SerperNewsData,
    SerperNewsResponse,
    SerperNewsResult,
    WebSearchData,
    WebSearchResponse,
)

try:
    import httpx
except ImportError as err:
    raise ImportError(
        "httpx is required for Serper tools. Install with: pip install httpx"
    ) from err

logger = logging.getLogger("humcp.tools.serper")

SERPER_SEARCH_URL = "https://google.serper.dev/search"
SERPER_NEWS_URL = "https://google.serper.dev/news"
SERPER_IMAGES_URL = "https://google.serper.dev/images"


@tool()
async def serper_google_search(
    query: str,
    num_results: int = 10,
    location: str = "us",
    language: str = "en",
) -> WebSearchResponse:
    """Search Google using the Serper.dev API.

    Args:
        query: The search query to look up.
        num_results: Number of results to return.
        location: Google location code for search results (e.g., "us", "uk").
        language: Language code for search results (e.g., "en", "fr").

    Returns:
        Search results with titles, URLs, and snippets.
    """
    try:
        api_key = await resolve_credential("SERPER_API_KEY")
        if not api_key:
            return WebSearchResponse(
                success=False,
                error="Serper API not configured. Set SERPER_API_KEY environment variable.",
            )

        if not query:
            return WebSearchResponse(
                success=False, error="Please provide a query to search for."
            )

        logger.info(
            "Serper search query_length=%d num_results=%d", len(query), num_results
        )

        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "q": query,
            "num": num_results,
            "gl": location,
            "hl": language,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                SERPER_SEARCH_URL, headers=headers, json=payload, timeout=30.0
            )
            response.raise_for_status()
            response_data = response.json()

        organic = response_data.get("organic", [])
        search_results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("link", ""),
                snippet=r.get("snippet", ""),
                score=r.get("position"),
            )
            for r in organic
        ]

        data = WebSearchData(
            query=query,
            results=search_results,
            total_results=len(search_results),
        )

        logger.info("Serper search complete results=%d", len(search_results))
        return WebSearchResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Serper search failed")
        return WebSearchResponse(success=False, error=f"Serper search failed: {str(e)}")


@tool()
async def serper_news_search(
    query: str,
    num_results: int = 10,
    location: str = "us",
    language: str = "en",
) -> SerperNewsResponse:
    """Search for news articles using the Serper.dev News API.

    Args:
        query: The news search query.
        num_results: Number of results to return.
        location: Country code for geolocation (e.g., "us", "uk").
        language: Language code (e.g., "en", "fr").

    Returns:
        News results with titles, URLs, snippets, dates, and sources.
    """
    try:
        api_key = await resolve_credential("SERPER_API_KEY")
        if not api_key:
            return SerperNewsResponse(
                success=False,
                error="Serper API not configured. Set SERPER_API_KEY environment variable.",
            )

        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": num_results, "gl": location, "hl": language}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                SERPER_NEWS_URL, headers=headers, json=payload, timeout=30.0
            )
            response.raise_for_status()
            response_data = response.json()

        news_results = [
            SerperNewsResult(
                title=r.get("title", ""),
                link=r.get("link", ""),
                snippet=r.get("snippet", ""),
                date=r.get("date"),
                source=r.get("source"),
            )
            for r in response_data.get("news", [])
        ]

        data = SerperNewsData(query=query, results=news_results)
        return SerperNewsResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Serper news search failed")
        return SerperNewsResponse(
            success=False, error=f"Serper news search failed: {str(e)}"
        )


@tool()
async def serper_image_search(
    query: str,
    num_results: int = 10,
    location: str = "us",
    language: str = "en",
) -> SerperImagesResponse:
    """Search for images using the Serper.dev Images API.

    Args:
        query: The image search query.
        num_results: Number of results to return.
        location: Country code for geolocation (e.g., "us", "uk").
        language: Language code (e.g., "en", "fr").

    Returns:
        Image results with titles, page URLs, and image URLs.
    """
    try:
        api_key = await resolve_credential("SERPER_API_KEY")
        if not api_key:
            return SerperImagesResponse(
                success=False,
                error="Serper API not configured. Set SERPER_API_KEY environment variable.",
            )

        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": num_results, "gl": location, "hl": language}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                SERPER_IMAGES_URL, headers=headers, json=payload, timeout=30.0
            )
            response.raise_for_status()
            response_data = response.json()

        image_results = [
            SerperImageResult(
                title=r.get("title", ""),
                link=r.get("link", ""),
                image_url=r.get("imageUrl", ""),
                source=r.get("source"),
            )
            for r in response_data.get("images", [])
        ]

        data = SerperImagesData(query=query, results=image_results)
        return SerperImagesResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Serper image search failed")
        return SerperImagesResponse(
            success=False, error=f"Serper image search failed: {str(e)}"
        )
