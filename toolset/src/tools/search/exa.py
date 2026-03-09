from __future__ import annotations

import logging
import os

from src.humcp.decorator import tool
from src.tools.search.schemas import (
    ExaFindSimilarData,
    ExaFindSimilarResponse,
    ExaSearchData,
    ExaSearchResponse,
    ExaSearchResult,
)

try:
    from exa_py import Exa
except ImportError as err:
    raise ImportError(
        "exa_py is required for Exa search tools. Install with: pip install exa_py"
    ) from err

logger = logging.getLogger("humcp.tools.exa")


@tool()
async def exa_search(
    query: str,
    num_results: int = 5,
    use_autoprompt: bool = True,
    text_length_limit: int = 1000,
    category: str | None = None,
) -> ExaSearchResponse:
    """Search the web using Exa, an AI-native search engine.

    Args:
        query: The search query to look up.
        num_results: Number of results to return.
        use_autoprompt: Let Exa automatically optimize the search query.
        text_length_limit: Maximum length of text content per result.
        category: Filter results by category. Options: "company", "research paper",
            "news", "pdf", "github", "tweet", "personal site", "linkedin profile",
            "financial report".

    Returns:
        Search results with titles, URLs, text content, and metadata.
    """
    try:
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            return ExaSearchResponse(
                success=False,
                error="Exa API not configured. Set EXA_API_KEY environment variable.",
            )

        if not query:
            return ExaSearchResponse(
                success=False, error="Please provide a query to search for."
            )

        logger.info(
            "Exa search query_length=%d num_results=%d autoprompt=%s",
            len(query),
            num_results,
            use_autoprompt,
        )

        exa_client = Exa(api_key)

        search_kwargs: dict = {
            "num_results": num_results,
            "text": True,
            "use_autoprompt": use_autoprompt,
        }
        if category:
            search_kwargs["category"] = category

        exa_results = exa_client.search_and_contents(query, **search_kwargs)

        search_results = []
        for result in exa_results.results:
            text = getattr(result, "text", "") or ""
            if text_length_limit and len(text) > text_length_limit:
                text = text[:text_length_limit]

            search_results.append(
                ExaSearchResult(
                    title=getattr(result, "title", "") or "",
                    url=result.url,
                    snippet=text,
                    author=getattr(result, "author", None),
                    published_date=getattr(result, "published_date", None),
                    score=getattr(result, "score", None),
                )
            )

        autoprompt = getattr(exa_results, "autoprompt_string", None)

        data = ExaSearchData(
            query=query,
            results=search_results,
            autoprompt_string=autoprompt,
        )

        logger.info("Exa search complete results=%d", len(search_results))
        return ExaSearchResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Exa search failed")
        return ExaSearchResponse(success=False, error=f"Exa search failed: {str(e)}")


@tool()
async def exa_find_similar(
    url: str,
    num_results: int = 5,
    text_length_limit: int = 1000,
    exclude_source_domain: bool = False,
) -> ExaFindSimilarResponse:
    """Find web pages similar to a given URL using Exa.

    Args:
        url: The URL to find similar pages for.
        num_results: Number of similar results to return.
        text_length_limit: Maximum length of text content per result.
        exclude_source_domain: Exclude results from the same domain as the source URL.

    Returns:
        Pages similar to the input URL with titles, URLs, and content.
    """
    try:
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            return ExaFindSimilarResponse(
                success=False,
                error="Exa API not configured. Set EXA_API_KEY environment variable.",
            )

        if not url:
            return ExaFindSimilarResponse(
                success=False, error="Please provide a URL to find similar pages."
            )

        logger.info("Exa find_similar url=%s num_results=%d", url, num_results)

        exa_client = Exa(api_key)
        exa_results = exa_client.find_similar_and_contents(
            url,
            num_results=num_results,
            text=True,
            exclude_source_domain=exclude_source_domain,
        )

        search_results = []
        for result in exa_results.results:
            text = getattr(result, "text", "") or ""
            if text_length_limit and len(text) > text_length_limit:
                text = text[:text_length_limit]

            search_results.append(
                ExaSearchResult(
                    title=getattr(result, "title", "") or "",
                    url=result.url,
                    snippet=text,
                    author=getattr(result, "author", None),
                    published_date=getattr(result, "published_date", None),
                    score=getattr(result, "score", None),
                )
            )

        data = ExaFindSimilarData(url=url, results=search_results)
        logger.info("Exa find_similar complete results=%d", len(search_results))
        return ExaFindSimilarResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Exa find_similar failed")
        return ExaFindSimilarResponse(
            success=False, error=f"Exa find_similar failed: {str(e)}"
        )
