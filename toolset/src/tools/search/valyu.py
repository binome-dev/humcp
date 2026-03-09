from __future__ import annotations

import logging
import os

from src.humcp.decorator import tool
from src.tools.search.schemas import (
    ValyuSearchData,
    ValyuSearchResponse,
    ValyuSearchResult,
)

try:
    from valyu import Valyu
except ImportError as err:
    raise ImportError(
        "valyu is required for Valyu search tools. Install with: pip install valyu"
    ) from err

logger = logging.getLogger("humcp.tools.valyu")


@tool()
async def valyu_search(
    query: str,
    search_type: str = "web",
    max_results: int = 10,
    max_price: float = 30.0,
    content_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> ValyuSearchResponse:
    """Search using the Valyu API for web and academic content.

    Args:
        query: The search query to look up.
        search_type: Type of search: "web" for web sources, "proprietary" for academic/proprietary sources.
        max_results: Maximum number of results to return.
        max_price: Maximum price for the API call.
        content_category: Description of the category of the query for filtering.
        start_date: Filter content after this date (YYYY-MM-DD).
        end_date: Filter content before this date (YYYY-MM-DD).

    Returns:
        Search results with titles, URLs, snippets, sources, and relevance scores.
    """
    try:
        api_key = os.getenv("VALYU_API_KEY")
        if not api_key:
            return ValyuSearchResponse(
                success=False,
                error="Valyu API not configured. Set VALYU_API_KEY environment variable.",
            )

        if not query:
            return ValyuSearchResponse(
                success=False, error="Please provide a query to search for."
            )

        if max_results < 1:
            return ValyuSearchResponse(
                success=False, error="max_results must be at least 1"
            )

        logger.info(
            "Valyu search query_length=%d search_type=%s max_results=%d",
            len(query),
            search_type,
            max_results,
        )

        valyu_client = Valyu(api_key=api_key)

        search_params: dict = {
            "query": query,
            "search_type": search_type,
            "max_num_results": max_results,
            "max_price": max_price,
        }
        if content_category:
            search_params["category"] = content_category
        if start_date:
            search_params["start_date"] = start_date
        if end_date:
            search_params["end_date"] = end_date

        response = valyu_client.search(**search_params)

        if not response.success:
            error_msg = getattr(response, "error", None) or "Search request failed"
            return ValyuSearchResponse(success=False, error=str(error_msg))

        search_results = []
        for r in response.results or []:
            content = getattr(r, "content", "") or ""
            description = getattr(r, "description", "") or ""
            snippet = content[:1000] if content else description

            search_results.append(
                ValyuSearchResult(
                    title=getattr(r, "title", None),
                    url=getattr(r, "url", None),
                    snippet=snippet or None,
                    source=getattr(r, "source", None),
                    relevance_score=getattr(r, "relevance_score", None),
                )
            )

        data = ValyuSearchData(
            query=query,
            search_type=search_type,
            results=search_results,
        )

        logger.info("Valyu search complete results=%d", len(search_results))
        return ValyuSearchResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Valyu search failed")
        return ValyuSearchResponse(
            success=False, error=f"Valyu search failed: {str(e)}"
        )
