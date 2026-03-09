from __future__ import annotations

import logging

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.search.schemas import (
    BraveImageResult,
    BraveImagesData,
    BraveImagesResponse,
    BraveNewsData,
    BraveNewsResponse,
    BraveNewsResult,
    SearchResult,
    WebSearchData,
    WebSearchResponse,
)

try:
    import httpx
except ImportError as err:
    raise ImportError(
        "httpx is required for Brave Search tools. Install with: pip install httpx"
    ) from err

logger = logging.getLogger("humcp.tools.brave")

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
BRAVE_NEWS_URL = "https://api.search.brave.com/res/v1/news/search"
BRAVE_IMAGES_URL = "https://api.search.brave.com/res/v1/images/search"


@tool()
async def brave_web_search(
    query: str,
    count: int = 5,
    country: str = "US",
    search_lang: str = "en",
) -> WebSearchResponse:
    """Search the web using the Brave Search API.

    Args:
        query: The search query to look up.
        count: Number of results to return (max 20).
        country: Country code for search results (e.g., "US", "GB").
        search_lang: Language code for search results (e.g., "en", "fr").

    Returns:
        Search results with titles, URLs, and snippets.
    """
    try:
        api_key = await resolve_credential("BRAVE_API_KEY")
        if not api_key:
            return WebSearchResponse(
                success=False,
                error="Brave Search API not configured. Set BRAVE_API_KEY environment variable.",
            )

        if not query:
            return WebSearchResponse(
                success=False, error="Please provide a query to search for."
            )

        if count < 1:
            return WebSearchResponse(success=False, error="count must be at least 1")

        logger.info(
            "Brave search query_length=%d count=%d country=%s",
            len(query),
            count,
            country,
        )

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        params = {
            "q": query,
            "count": min(count, 20),
            "country": country,
            "search_lang": search_lang,
            "result_filter": "web",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                BRAVE_SEARCH_URL, headers=headers, params=params, timeout=30.0
            )
            response.raise_for_status()
            response_data = response.json()

        search_results = []
        web_results = response_data.get("web", {}).get("results", [])
        for r in web_results:
            search_results.append(
                SearchResult(
                    title=r.get("title", ""),
                    url=str(r.get("url", "")),
                    snippet=r.get("description", ""),
                )
            )

        data = WebSearchData(
            query=query,
            results=search_results,
            total_results=len(search_results),
        )

        logger.info("Brave search complete results=%d", len(search_results))
        return WebSearchResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Brave search failed")
        return WebSearchResponse(success=False, error=f"Brave search failed: {str(e)}")


@tool()
async def brave_news_search(
    query: str,
    count: int = 5,
    country: str = "US",
    search_lang: str = "en",
    freshness: str | None = None,
) -> BraveNewsResponse:
    """Search for news articles using the Brave Search News API.

    Args:
        query: The news search query.
        count: Number of results to return (max 20).
        country: Country code for results (e.g., "US", "GB").
        search_lang: Language code (e.g., "en", "fr").
        freshness: Time filter: "pd" (past day), "pw" (past week), "pm" (past month), "py" (past year).

    Returns:
        News results with titles, URLs, descriptions, and sources.
    """
    try:
        api_key = await resolve_credential("BRAVE_API_KEY")
        if not api_key:
            return BraveNewsResponse(
                success=False,
                error="Brave Search API not configured. Set BRAVE_API_KEY environment variable.",
            )

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        params: dict = {
            "q": query,
            "count": min(count, 20),
            "country": country,
            "search_lang": search_lang,
        }
        if freshness:
            params["freshness"] = freshness

        async with httpx.AsyncClient() as client:
            response = await client.get(
                BRAVE_NEWS_URL, headers=headers, params=params, timeout=30.0
            )
            response.raise_for_status()
            response_data = response.json()

        news_results = []
        for r in response_data.get("results", []):
            news_results.append(
                BraveNewsResult(
                    title=r.get("title", ""),
                    url=str(r.get("url", "")),
                    description=r.get("description", ""),
                    age=r.get("age"),
                    source=r.get("meta_url", {}).get("hostname")
                    if isinstance(r.get("meta_url"), dict)
                    else None,
                )
            )

        data = BraveNewsData(query=query, results=news_results)
        return BraveNewsResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Brave news search failed")
        return BraveNewsResponse(
            success=False, error=f"Brave news search failed: {str(e)}"
        )


@tool()
async def brave_image_search(
    query: str,
    count: int = 5,
    country: str = "US",
    search_lang: str = "en",
    safesearch: str = "moderate",
) -> BraveImagesResponse:
    """Search for images using the Brave Search Images API.

    Args:
        query: The image search query.
        count: Number of results to return (max 20).
        country: Country code for results (e.g., "US", "GB").
        search_lang: Language code (e.g., "en", "fr").
        safesearch: Safe search level: "off", "moderate", "strict".

    Returns:
        Image results with titles, page URLs, and thumbnail URLs.
    """
    try:
        api_key = await resolve_credential("BRAVE_API_KEY")
        if not api_key:
            return BraveImagesResponse(
                success=False,
                error="Brave Search API not configured. Set BRAVE_API_KEY environment variable.",
            )

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        params = {
            "q": query,
            "count": min(count, 20),
            "country": country,
            "search_lang": search_lang,
            "safesearch": safesearch,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                BRAVE_IMAGES_URL, headers=headers, params=params, timeout=30.0
            )
            response.raise_for_status()
            response_data = response.json()

        image_results = []
        for r in response_data.get("results", []):
            image_results.append(
                BraveImageResult(
                    title=r.get("title", ""),
                    url=str(r.get("url", "")),
                    thumbnail_url=r.get("thumbnail", {}).get("src", "")
                    if isinstance(r.get("thumbnail"), dict)
                    else "",
                    source=r.get("source"),
                )
            )

        data = BraveImagesData(query=query, results=image_results)
        return BraveImagesResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Brave image search failed")
        return BraveImagesResponse(
            success=False, error=f"Brave image search failed: {str(e)}"
        )
