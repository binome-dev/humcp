from __future__ import annotations

import logging
from typing import Literal

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.search.schemas import (
    ExaAnswerData,
    ExaAnswerResponse,
    ExaFindSimilarData,
    ExaFindSimilarResponse,
    ExaGetContentsData,
    ExaGetContentsResponse,
    ExaSearchData,
    ExaSearchResponse,
    ExaSearchResult,
)

try:
    from exa_py import Exa
    from exa_py.api import (
        ContentsOptions,
        HighlightsContentsOptions,
        TextContentsOptions,
    )
except ImportError as err:
    raise ImportError(
        "exa_py is required for Exa search tools. Install with: pip install exa_py"
    ) from err

logger = logging.getLogger("humcp.tools.exa")


def _build_result(result: object, max_characters: int) -> ExaSearchResult:
    """Extract fields from an Exa SDK result object into our schema."""
    text = getattr(result, "text", "") or ""
    if max_characters and len(text) > max_characters:
        text = text[:max_characters]

    raw_highlights = getattr(result, "highlights", None)
    highlights = list(raw_highlights) if raw_highlights else None

    return ExaSearchResult(
        title=getattr(result, "title", "") or "",
        url=getattr(result, "url", "") or "",
        snippet=text,
        highlights=highlights,
        author=getattr(result, "author", None),
        published_date=getattr(result, "published_date", None),
        score=getattr(result, "score", None),
    )


def _build_contents(
    content_type: str,
    max_characters: int,
    livecrawl: str | None = None,
) -> ContentsOptions:
    """Build the contents parameter for Exa API calls."""
    opts = ContentsOptions()
    if content_type == "highlights":
        opts["highlights"] = HighlightsContentsOptions(max_characters=max_characters)
    else:
        opts["text"] = TextContentsOptions(max_characters=max_characters)
    if livecrawl:
        opts["livecrawl"] = livecrawl  # type: ignore[typeddict-item]
    return opts


@tool()
async def exa_search(
    query: str,
    num_results: int = 10,
    search_type: Literal["auto", "fast"] = "auto",
    content_type: Literal["highlights", "text"] = "highlights",
    max_characters: int = 4000,
    category: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    livecrawl: Literal["preferred", "always", "never"] | None = None,
) -> ExaSearchResponse:
    """Search the web using Exa, an AI-native search engine.

    Args:
        query: The search query to look up.
        num_results: Number of results to return (max 100).
        search_type: Search mode — "auto" for balanced relevance and speed,
            "fast" for real-time apps and quick lookups.
        content_type: Content extraction mode — "highlights" for key excerpts
            (lower cost), "text" for full contiguous content (higher cost).
        max_characters: Maximum characters of content per result.
        category: Filter results by category. Options: "company", "research paper",
            "news", "tweet", "people", "pdf", "github", "personal site",
            "linkedin profile", "financial report".
        include_domains: Only return results from these domains (e.g. ["arxiv.org"]).
        exclude_domains: Exclude results from these domains (e.g. ["pinterest.com"]).
        livecrawl: Content freshness — "preferred" to livecrawl if cache is stale,
            "always" to always livecrawl, "never" for cache only.

    Returns:
        Search results with titles, URLs, content, and metadata.
    """
    try:
        api_key = await resolve_credential("EXA_API_KEY")
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
            "Exa search query_length=%d num_results=%d type=%s content=%s",
            len(query),
            num_results,
            search_type,
            content_type,
        )

        exa_client = Exa(api_key)

        search_kwargs: dict = {
            "num_results": num_results,
            "type": search_type,
            "contents": _build_contents(content_type, max_characters, livecrawl),
        }
        if category:
            search_kwargs["category"] = category
        if include_domains:
            search_kwargs["include_domains"] = include_domains
        if exclude_domains:
            search_kwargs["exclude_domains"] = exclude_domains

        exa_results = exa_client.search(query, **search_kwargs)

        search_results = [_build_result(r, max_characters) for r in exa_results.results]

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
        return ExaSearchResponse(success=False, error=f"Exa search failed: {e!s}")


@tool()
async def exa_find_similar(
    url: str,
    num_results: int = 10,
    content_type: Literal["highlights", "text"] = "highlights",
    max_characters: int = 4000,
    exclude_source_domain: bool = False,
) -> ExaFindSimilarResponse:
    """Find web pages similar to a given URL using Exa.

    Args:
        url: The URL to find similar pages for.
        num_results: Number of similar results to return.
        content_type: Content extraction mode — "highlights" for key excerpts,
            "text" for full content.
        max_characters: Maximum characters of content per result.
        exclude_source_domain: Exclude results from the same domain as the source URL.

    Returns:
        Pages similar to the input URL with titles, URLs, and content.
    """
    try:
        api_key = await resolve_credential("EXA_API_KEY")
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
        exa_results = exa_client.find_similar(
            url,
            num_results=num_results,
            exclude_source_domain=exclude_source_domain,
            contents=_build_contents(content_type, max_characters),
        )

        search_results = [_build_result(r, max_characters) for r in exa_results.results]

        data = ExaFindSimilarData(url=url, results=search_results)
        logger.info("Exa find_similar complete results=%d", len(search_results))
        return ExaFindSimilarResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Exa find_similar failed")
        return ExaFindSimilarResponse(
            success=False, error=f"Exa find_similar failed: {e!s}"
        )


@tool()
async def exa_get_contents(
    urls: list[str],
    content_type: Literal["highlights", "text"] = "text",
    max_characters: int = 20000,
) -> ExaGetContentsResponse:
    """Get content from specific URLs using Exa.

    Use this to extract text or highlights from known URLs without searching.

    Args:
        urls: List of URLs to extract content from.
        content_type: Content extraction mode — "text" for full contiguous content,
            "highlights" for key excerpts.
        max_characters: Maximum characters of content per URL.

    Returns:
        Extracted content for each URL.
    """
    try:
        api_key = await resolve_credential("EXA_API_KEY")
        if not api_key:
            return ExaGetContentsResponse(
                success=False,
                error="Exa API not configured. Set EXA_API_KEY environment variable.",
            )

        if not urls:
            return ExaGetContentsResponse(
                success=False, error="Please provide at least one URL."
            )

        logger.info("Exa get_contents urls=%d", len(urls))

        exa_client = Exa(api_key)
        content_kwargs: dict = {}
        if content_type == "highlights":
            content_kwargs["highlights"] = HighlightsContentsOptions(
                max_characters=max_characters
            )
        else:
            content_kwargs["text"] = TextContentsOptions(max_characters=max_characters)
        exa_results = exa_client.get_contents(urls, **content_kwargs)

        results = [_build_result(r, max_characters) for r in exa_results.results]

        data = ExaGetContentsData(results=results)
        logger.info("Exa get_contents complete results=%d", len(results))
        return ExaGetContentsResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Exa get_contents failed")
        return ExaGetContentsResponse(
            success=False, error=f"Exa get_contents failed: {e!s}"
        )


@tool()
async def exa_answer(
    query: str,
) -> ExaAnswerResponse:
    """Ask a question and get an AI-generated answer with cited web sources using Exa.

    Best for factual questions that benefit from real-time web citations.

    Args:
        query: The question to answer.

    Returns:
        An AI-generated answer with source citations.
    """
    try:
        api_key = await resolve_credential("EXA_API_KEY")
        if not api_key:
            return ExaAnswerResponse(
                success=False,
                error="Exa API not configured. Set EXA_API_KEY environment variable.",
            )

        if not query:
            return ExaAnswerResponse(
                success=False, error="Please provide a question to answer."
            )

        logger.info("Exa answer query_length=%d", len(query))

        exa_client = Exa(api_key)
        exa_result = exa_client.answer(query, text=True)

        answer_text = getattr(exa_result, "answer", "") or ""
        if isinstance(answer_text, dict):
            answer_text = str(answer_text)
        raw_citations = getattr(exa_result, "citations", []) or []
        citations = [_build_result(r, 4000) for r in raw_citations]

        data = ExaAnswerData(
            query=query,
            answer=answer_text,
            citations=citations,
        )

        logger.info("Exa answer complete citations=%d", len(citations))
        return ExaAnswerResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Exa answer failed")
        return ExaAnswerResponse(success=False, error=f"Exa answer failed: {e!s}")
