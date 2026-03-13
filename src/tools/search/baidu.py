from __future__ import annotations

import logging

from src.humcp.decorator import tool
from src.tools.search.schemas import (
    SearchResult,
    WebSearchData,
    WebSearchResponse,
)

try:
    from baidusearch.baidusearch import search as baidu_raw_search  # type: ignore
except ImportError as err:
    raise ImportError(
        "baidusearch is required for Baidu search tools. "
        "Install with: pip install baidusearch"
    ) from err

logger = logging.getLogger("humcp.tools.baidu")


@tool()
async def baidu_search(
    query: str,
    max_results: int = 5,
) -> WebSearchResponse:
    """Search the web using Baidu, the leading Chinese search engine.

    Args:
        query: The search query (supports Chinese and English).
        max_results: Maximum number of results to return.

    Returns:
        Search results with titles, URLs, and snippets.
    """
    try:
        if not query:
            return WebSearchResponse(
                success=False, error="Please provide a query to search for."
            )

        if max_results < 1:
            return WebSearchResponse(
                success=False, error="max_results must be at least 1"
            )

        logger.info(
            "Baidu search query_length=%d max_results=%d", len(query), max_results
        )

        raw_results = baidu_raw_search(keyword=query, num_results=max_results)

        search_results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("abstract", ""),
            )
            for r in raw_results
        ]

        data = WebSearchData(
            query=query,
            results=search_results,
            total_results=len(search_results),
        )

        logger.info("Baidu search complete results=%d", len(search_results))
        return WebSearchResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Baidu search failed")
        return WebSearchResponse(success=False, error=f"Baidu search failed: {str(e)}")
