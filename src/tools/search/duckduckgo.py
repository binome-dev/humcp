from __future__ import annotations

import logging
import os

from src.humcp.decorator import tool
from src.tools.search.schemas import (
    DuckDuckGoImageResult,
    DuckDuckGoImagesData,
    DuckDuckGoImagesResponse,
    DuckDuckGoNewsData,
    DuckDuckGoNewsResponse,
    DuckDuckGoNewsResult,
    SearchResult,
    WebSearchData,
    WebSearchResponse,
)

try:
    from duckduckgo_search import DDGS
except ImportError as err:
    raise ImportError(
        "duckduckgo-search is required for DuckDuckGo tools. "
        "Install with: pip install duckduckgo-search"
    ) from err

logger = logging.getLogger("humcp.tools.duckduckgo")


@tool()
async def duckduckgo_search(
    query: str,
    max_results: int = 5,
    timelimit: str | None = None,
    region: str = "wt-wt",
) -> WebSearchResponse:
    """Search the web using DuckDuckGo and return results.

    Args:
        query: The search query to look up.
        max_results: Maximum number of results to return.
        timelimit: Time limit for results: "d" (day), "w" (week), "m" (month), "y" (year).
        region: Region for search results (e.g., "wt-wt" for worldwide, "us-en", "uk-en").

    Returns:
        Search results with titles, URLs, and snippets.
    """
    try:
        if max_results < 1:
            return WebSearchResponse(
                success=False, error="max_results must be at least 1"
            )

        proxy = os.getenv("DUCKDUCKGO_PROXY")
        logger.info(
            "DuckDuckGo search query_length=%d max_results=%d region=%s",
            len(query),
            max_results,
            region,
        )

        with DDGS(proxy=proxy) as ddgs:
            raw_results = list(
                ddgs.text(
                    keywords=query,
                    region=region,
                    timelimit=timelimit,
                    max_results=max_results,
                )
            )

        search_results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("href", r.get("link", "")),
                snippet=r.get("body", r.get("snippet", "")),
            )
            for r in raw_results
        ]

        data = WebSearchData(
            query=query,
            results=search_results,
            total_results=len(search_results),
        )

        logger.info("DuckDuckGo search complete results=%d", len(search_results))
        return WebSearchResponse(success=True, data=data)
    except Exception as e:
        logger.exception("DuckDuckGo search failed")
        return WebSearchResponse(
            success=False, error=f"DuckDuckGo search failed: {str(e)}"
        )


@tool()
async def duckduckgo_news(
    query: str,
    max_results: int = 5,
    timelimit: str | None = None,
    region: str = "wt-wt",
) -> DuckDuckGoNewsResponse:
    """Search for news articles using DuckDuckGo News.

    Args:
        query: The news search query.
        max_results: Maximum number of news results to return.
        timelimit: Time limit for results: "d" (day), "w" (week), "m" (month).
        region: Region for search results (e.g., "wt-wt" for worldwide, "us-en").

    Returns:
        News results with titles, URLs, snippets, sources, and dates.
    """
    try:
        if max_results < 1:
            return DuckDuckGoNewsResponse(
                success=False, error="max_results must be at least 1"
            )

        proxy = os.getenv("DUCKDUCKGO_PROXY")
        logger.info(
            "DuckDuckGo news search query_length=%d max_results=%d",
            len(query),
            max_results,
        )

        with DDGS(proxy=proxy) as ddgs:
            raw_results = list(
                ddgs.news(
                    keywords=query,
                    region=region,
                    timelimit=timelimit,
                    max_results=max_results,
                )
            )

        news_results = [
            DuckDuckGoNewsResult(
                title=r.get("title", ""),
                url=r.get("url", r.get("link", "")),
                snippet=r.get("body", r.get("snippet", "")),
                source=r.get("source"),
                date=r.get("date"),
            )
            for r in raw_results
        ]

        data = DuckDuckGoNewsData(query=query, results=news_results)

        logger.info("DuckDuckGo news search complete results=%d", len(news_results))
        return DuckDuckGoNewsResponse(success=True, data=data)
    except Exception as e:
        logger.exception("DuckDuckGo news search failed")
        return DuckDuckGoNewsResponse(
            success=False, error=f"DuckDuckGo news search failed: {str(e)}"
        )


@tool()
async def duckduckgo_images(
    query: str,
    max_results: int = 5,
    region: str = "wt-wt",
    safesearch: str = "moderate",
    size: str | None = None,
    color: str | None = None,
    type_image: str | None = None,
) -> DuckDuckGoImagesResponse:
    """Search for images using DuckDuckGo.

    Args:
        query: The image search query.
        max_results: Maximum number of image results to return.
        region: Region for results (e.g., "wt-wt" worldwide, "us-en").
        safesearch: Safe search level: "on", "moderate", "off".
        size: Filter by size: "Small", "Medium", "Large", "Wallpaper".
        color: Filter by color: "color", "Monochrome", "Red", "Orange", "Yellow",
            "Green", "Blue", "Purple", "Pink", "Brown", "Black", "Gray", "Teal", "White".
        type_image: Filter by type: "photo", "clipart", "gif", "transparent", "line".

    Returns:
        Image results with titles, page URLs, image URLs, and dimensions.
    """
    try:
        if max_results < 1:
            return DuckDuckGoImagesResponse(
                success=False, error="max_results must be at least 1"
            )

        proxy = os.getenv("DUCKDUCKGO_PROXY")
        logger.info(
            "DuckDuckGo images query_length=%d max_results=%d", len(query), max_results
        )

        with DDGS(proxy=proxy) as ddgs:
            raw_results = list(
                ddgs.images(
                    keywords=query,
                    region=region,
                    safesearch=safesearch,
                    size=size,
                    color=color,
                    type_image=type_image,
                    max_results=max_results,
                )
            )

        image_results = [
            DuckDuckGoImageResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                image_url=r.get("image", ""),
                thumbnail_url=r.get("thumbnail", ""),
                source=r.get("source"),
                width=r.get("width"),
                height=r.get("height"),
            )
            for r in raw_results
        ]

        data = DuckDuckGoImagesData(query=query, results=image_results)
        logger.info("DuckDuckGo images complete results=%d", len(image_results))
        return DuckDuckGoImagesResponse(success=True, data=data)
    except Exception as e:
        logger.exception("DuckDuckGo images search failed")
        return DuckDuckGoImagesResponse(
            success=False, error=f"DuckDuckGo images search failed: {str(e)}"
        )
