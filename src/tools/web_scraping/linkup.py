"""Web search tool using Linkup API."""

from __future__ import annotations

import logging

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.web_scraping.schemas import (
    SearchResponse,
    SearchResultData,
    SearchResultItem,
)

logger = logging.getLogger("humcp.tools.linkup")


@tool()
async def linkup_search(
    query: str,
    depth: str = "standard",
    output_type: str = "searchResults",
) -> SearchResponse:
    """Search the web using Linkup API for real-time information.

    Provides real-time online information using the Linkup search service.
    Requires LINKUP_API_KEY.

    Args:
        query: The search query.
        depth: Search depth - 'standard' or 'deep'. Defaults to 'standard'.
        output_type: Output type - 'searchResults' or 'sourcedAnswer'. Defaults to 'searchResults'.

    Returns:
        Search results with titles, URLs, and content.
    """
    try:
        try:
            from linkup import LinkupClient
        except ImportError as err:
            raise ImportError(
                "linkup-sdk is required for Linkup tools. "
                "Install with: pip install linkup-sdk"
            ) from err

        api_key = await resolve_credential("LINKUP_API_KEY")
        if not api_key:
            return SearchResponse(
                success=False,
                error="Linkup API not configured. Set LINKUP_API_KEY.",
            )

        if not query:
            return SearchResponse(success=False, error="Query is required")

        logger.info("Linkup search start query=%s depth=%s", query, depth)

        client = LinkupClient(api_key=api_key)
        response = client.search(
            query=query,
            depth=depth,
            output_type=output_type,
        )

        items = []
        if isinstance(response, str):
            items.append(
                SearchResultItem(
                    title=None,
                    url="",
                    content=response,
                )
            )
        elif hasattr(response, "results"):
            for r in response.results:
                items.append(
                    SearchResultItem(
                        title=getattr(r, "title", None),
                        url=getattr(r, "url", ""),
                        content=getattr(r, "content", getattr(r, "snippet", "")),
                        score=getattr(r, "score", None),
                    )
                )

        data = SearchResultData(query=query, results=items)

        logger.info("Linkup search complete query=%s results=%d", query, len(items))
        return SearchResponse(success=True, data=data)

    except ImportError:
        raise
    except Exception as e:
        logger.exception("Linkup search failed")
        return SearchResponse(success=False, error=f"Linkup search failed: {str(e)}")
