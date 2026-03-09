from __future__ import annotations

import logging
import os
from typing import Any

from src.humcp.decorator import tool
from src.tools.search.schemas import (
    SeltzSearchData,
    SeltzSearchResponse,
    SeltzSearchResult,
)

try:
    from seltz import Includes, Seltz
except ImportError as err:
    raise ImportError(
        "seltz is required for Seltz search tools. Install with: pip install seltz"
    ) from err

logger = logging.getLogger("humcp.tools.seltz")


def _parse_document(doc: Any) -> dict:
    """Parse a Seltz document into a dictionary."""
    if hasattr(doc, "to_dict"):
        return doc.to_dict()
    doc_dict: dict[str, Any] = {}
    url = getattr(doc, "url", None)
    content = getattr(doc, "content", None)
    title = getattr(doc, "title", None)
    score = getattr(doc, "score", None)
    if url is not None:
        doc_dict["url"] = url
    if content:
        doc_dict["content"] = content
    if title:
        doc_dict["title"] = title
    if score is not None:
        doc_dict["score"] = score
    return doc_dict


@tool()
async def seltz_search(
    query: str,
    max_results: int = 10,
    context: str | None = None,
) -> SeltzSearchResponse:
    """Search using the Seltz AI-powered search API.

    Args:
        query: The search query to look up.
        max_results: Maximum number of documents to return.
        context: Additional context to improve search quality (e.g., "user is looking for Python docs").

    Returns:
        Search results with URLs, content, and metadata.
    """
    try:
        api_key = os.getenv("SELTZ_API_KEY")
        if not api_key:
            return SeltzSearchResponse(
                success=False,
                error="Seltz API not configured. Set SELTZ_API_KEY environment variable.",
            )

        if not query:
            return SeltzSearchResponse(
                success=False, error="Please provide a query to search for."
            )

        if max_results < 1:
            return SeltzSearchResponse(
                success=False, error="max_results must be at least 1"
            )

        logger.info(
            "Seltz search query_length=%d max_results=%d", len(query), max_results
        )

        client = Seltz(api_key=api_key)
        includes = Includes(max_documents=max_results)
        response = client.search(
            query=query,
            includes=includes,
            context=context,
        )

        search_results = []
        for doc in response.documents or []:
            parsed = _parse_document(doc)
            if parsed:
                search_results.append(
                    SeltzSearchResult(
                        url=parsed.get("url"),
                        content=parsed.get("content"),
                        title=parsed.get("title"),
                        score=parsed.get("score"),
                    )
                )

        data = SeltzSearchData(query=query, results=search_results)

        logger.info("Seltz search complete results=%d", len(search_results))
        return SeltzSearchResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Seltz search failed")
        return SeltzSearchResponse(
            success=False, error=f"Seltz search failed: {str(e)}"
        )
