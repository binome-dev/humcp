from __future__ import annotations

import logging
import os
import urllib.parse

from src.humcp.decorator import tool
from src.tools.search.schemas import (
    SearchResult,
    WebSearchData,
    WebSearchResponse,
)

try:
    import httpx
except ImportError as err:
    raise ImportError(
        "httpx is required for SearXNG tools. Install with: pip install httpx"
    ) from err

logger = logging.getLogger("humcp.tools.searxng")


@tool()
async def searxng_search(
    query: str,
    categories: str | None = None,
    num_results: int = 5,
    engines: str | None = None,
) -> WebSearchResponse:
    """Search the web using a self-hosted SearXNG instance.

    Args:
        query: The search query to look up.
        categories: Search category (e.g., "general", "images", "news", "it", "science", "videos", "music", "map").
        num_results: Maximum number of results to return.
        engines: Comma-separated list of specific engines to use (e.g., "google,duckduckgo").

    Returns:
        Search results with titles, URLs, and snippets.
    """
    try:
        base_url = os.getenv("SEARXNG_BASE_URL")
        if not base_url:
            return WebSearchResponse(
                success=False,
                error="SearXNG not configured. Set SEARXNG_BASE_URL environment variable.",
            )

        if not query:
            return WebSearchResponse(
                success=False, error="Please provide a query to search for."
            )

        if num_results < 1:
            return WebSearchResponse(
                success=False, error="num_results must be at least 1"
            )

        logger.info(
            "SearXNG search query_length=%d categories=%s num_results=%d",
            len(query),
            categories,
            num_results,
        )

        encoded_query = urllib.parse.quote(query)
        url = f"{base_url.rstrip('/')}/search?format=json&q={encoded_query}"

        if categories:
            url += f"&categories={urllib.parse.quote(categories)}"
        if engines:
            url += f"&engines={urllib.parse.quote(engines)}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            response_data = response.json()

        raw_results = response_data.get("results", [])[:num_results]

        search_results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", ""),
                score=r.get("score"),
            )
            for r in raw_results
        ]

        data = WebSearchData(
            query=query,
            results=search_results,
            total_results=response_data.get("number_of_results"),
        )

        logger.info("SearXNG search complete results=%d", len(search_results))
        return WebSearchResponse(success=True, data=data)
    except Exception as e:
        logger.exception("SearXNG search failed")
        return WebSearchResponse(
            success=False, error=f"SearXNG search failed: {str(e)}"
        )
