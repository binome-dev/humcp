"""Web reading and search tools using Jina Reader API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.web_scraping.schemas import (
    ScrapedPageData,
    ScrapeResponse,
    SearchResponse,
    SearchResultData,
    SearchResultItem,
)

logger = logging.getLogger("humcp.tools.jina")

_JINA_READER_BASE_URL = "https://r.jina.ai/"
_JINA_SEARCH_URL = "https://s.jina.ai/"
_MAX_CONTENT_LENGTH = 10000


def _get_jina_headers(
    api_key: str | None = None,
    target_selector: str | None = None,
    return_format: str | None = None,
    include_links: bool = False,
) -> dict[str, str]:
    """Build request headers for Jina API calls."""
    headers = {
        "Accept": "application/json",
        "X-With-Links-Summary": "true",
        "X-With-Images-Summary": "true",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if target_selector:
        headers["X-Target-Selector"] = target_selector
    if return_format:
        headers["X-Return-Format"] = return_format
    if include_links:
        headers["X-Return-Links"] = "true"
    return headers


@tool()
async def jina_reader(
    url: str,
    max_content_length: int = _MAX_CONTENT_LENGTH,
    target_selector: str | None = None,
    return_format: str | None = None,
    include_links: bool = False,
) -> ScrapeResponse:
    """Read and extract content from a URL using Jina Reader API.

    Converts a web page to clean, readable content via Jina's r.jina.ai service.
    Works without an API key, but setting JINA_API_KEY provides higher rate limits.

    Args:
        url: The URL to read and extract content from.
        max_content_length: Maximum content length in characters. Defaults to 10000.
        target_selector: CSS selector to target specific page elements (e.g., 'article', '.main-content', '#post-body').
        return_format: Desired return format. Options: 'markdown', 'html', 'text', 'screenshot', 'pageshot'.
        include_links: Whether to include links found in the page in the response metadata. Defaults to False.

    Returns:
        Scraped page data with extracted content.
    """
    if not url:
        return ScrapeResponse(success=False, error="URL is required")

    try:
        logger.info("Jina reader start url=%s include_links=%s", url, include_links)

        api_key = await resolve_credential("JINA_API_KEY")

        full_url = f"{_JINA_READER_BASE_URL}{url}"
        headers = _get_jina_headers(
            api_key=api_key,
            target_selector=target_selector,
            return_format=return_format,
            include_links=include_links,
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(full_url, headers=headers, timeout=30.0)
            response.raise_for_status()

        result = response.json()

        content = ""
        title = None
        metadata: dict[str, Any] | None = None
        if isinstance(result, dict):
            content = result.get("content", result.get("text", str(result)))
            title = result.get("title")

            if include_links:
                links = result.get("links", result.get("linksOnPage"))
                if links:
                    metadata = {"links": links}
        else:
            content = str(result)

        if max_content_length and len(content) > max_content_length:
            content = content[:max_content_length] + "... (content truncated)"

        data = ScrapedPageData(
            url=url,
            title=title,
            content=content,
            markdown=None,
            metadata=metadata,
        )

        logger.info("Jina reader complete url=%s content_length=%d", url, len(content))
        return ScrapeResponse(success=True, data=data)

    except Exception as e:
        logger.exception("Jina reader failed")
        return ScrapeResponse(success=False, error=f"Jina reader failed: {str(e)}")


@tool()
async def jina_search(
    query: str,
    max_content_length: int = _MAX_CONTENT_LENGTH,
) -> SearchResponse:
    """Search the web using Jina Search API.

    Performs a web search and returns results via Jina's s.jina.ai service.
    Works without an API key, but setting JINA_API_KEY provides higher rate limits.

    Args:
        query: The search query.
        max_content_length: Maximum content length per result. Defaults to 10000.

    Returns:
        Search results with titles, URLs, and content snippets.
    """
    if not query:
        return SearchResponse(success=False, error="Query is required")

    try:
        logger.info("Jina search start query=%s", query)

        api_key = await resolve_credential("JINA_API_KEY")
        headers = _get_jina_headers(api_key=api_key)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                _JINA_SEARCH_URL,
                headers=headers,
                json={"q": query},
                timeout=30.0,
            )
            response.raise_for_status()

        result = response.json()

        items = []
        if isinstance(result, dict):
            results_list = result.get("results", result.get("data", []))
            if isinstance(results_list, list):
                for r in results_list:
                    if isinstance(r, dict):
                        content = r.get("content", r.get("description", ""))
                        if max_content_length and len(content) > max_content_length:
                            content = content[:max_content_length] + "..."
                        items.append(
                            SearchResultItem(
                                title=r.get("title"),
                                url=r.get("url", ""),
                                content=content,
                                score=r.get("score"),
                            )
                        )

        data = SearchResultData(query=query, results=items)

        logger.info("Jina search complete query=%s results=%d", query, len(items))
        return SearchResponse(success=True, data=data)

    except Exception as e:
        logger.exception("Jina search failed")
        return SearchResponse(success=False, error=f"Jina search failed: {str(e)}")
