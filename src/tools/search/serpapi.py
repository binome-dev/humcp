from __future__ import annotations

import logging

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.search.schemas import (
    SearchResult,
    SerpApiSearchData,
    SerpApiSearchResponse,
)

try:
    import serpapi as serpapi_lib
except ImportError as err:
    raise ImportError(
        "google-search-results is required for SerpAPI tools. "
        "Install with: pip install google-search-results"
    ) from err

logger = logging.getLogger("humcp.tools.serpapi")


@tool()
async def serpapi_search(
    query: str,
    engine: str = "google",
    num_results: int = 10,
) -> SerpApiSearchResponse:
    """Search the web using SerpAPI (supports Google, Bing, Yahoo, and more).

    Args:
        query: The search query to look up.
        engine: Search engine to use (e.g., "google", "bing", "yahoo"). Defaults to "google".
        num_results: Number of results to return.

    Returns:
        Search results with titles, URLs, snippets, knowledge graph, and related questions.
    """
    try:
        api_key = await resolve_credential("SERPAPI_API_KEY")
        if not api_key:
            return SerpApiSearchResponse(
                success=False,
                error="SerpAPI not configured. Set SERPAPI_API_KEY environment variable.",
            )

        if not query:
            return SerpApiSearchResponse(
                success=False, error="Please provide a query to search for."
            )

        logger.info(
            "SerpAPI search query_length=%d engine=%s num_results=%d",
            len(query),
            engine,
            num_results,
        )

        params = {
            "q": query,
            "api_key": api_key,
            "num": num_results,
        }

        search = serpapi_lib.GoogleSearch(params)
        results = search.get_dict()

        organic = results.get("organic_results", [])
        search_results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("link", ""),
                snippet=r.get("snippet", ""),
                score=r.get("position"),
            )
            for r in organic
        ]

        knowledge_graph = results.get("knowledge_graph")
        related_questions = results.get("related_questions")

        data = SerpApiSearchData(
            query=query,
            results=search_results,
            knowledge_graph=knowledge_graph,
            related_questions=related_questions,
        )

        logger.info("SerpAPI search complete results=%d", len(search_results))
        return SerpApiSearchResponse(success=True, data=data)
    except Exception as e:
        logger.exception("SerpAPI search failed")
        return SerpApiSearchResponse(
            success=False, error=f"SerpAPI search failed: {str(e)}"
        )
