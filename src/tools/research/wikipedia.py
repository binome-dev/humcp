"""Wikipedia search and page retrieval tools."""

from __future__ import annotations

import logging

from src.humcp.decorator import tool
from src.tools.research.schemas import (
    WikipediaGetPageResponse,
    WikipediaGetSummaryResponse,
    WikipediaPageData,
    WikipediaSearchData,
    WikipediaSearchResponse,
    WikipediaSearchResult,
    WikipediaSummaryData,
)

try:
    import wikipedia
except ImportError as err:
    raise ImportError(
        "wikipedia is required for Wikipedia tools. Install with: pip install wikipedia"
    ) from err

logger = logging.getLogger("humcp.tools.wikipedia")


@tool()
async def wikipedia_search(
    query: str,
    max_results: int = 5,
    language: str = "en",
) -> WikipediaSearchResponse:
    """Search Wikipedia for pages matching a query.

    Args:
        query: The search query to find Wikipedia pages.
        max_results: Maximum number of results to return (default 5, max 20).
        language: Wikipedia language code (e.g. "en", "fr", "de", "es", "ja", "zh"). Default is "en".

    Returns:
        A list of matching Wikipedia page titles with summaries.
    """
    try:
        if max_results < 1:
            return WikipediaSearchResponse(
                success=False, error="max_results must be at least 1"
            )

        max_results = min(max_results, 20)

        logger.info(
            "Wikipedia search query_length=%d max_results=%d lang=%s",
            len(query),
            max_results,
            language,
        )

        wikipedia.set_lang(language)
        titles = wikipedia.search(query, results=max_results)

        results: list[WikipediaSearchResult] = []
        for title in titles:
            try:
                summary = wikipedia.summary(title, sentences=2)
                url = wikipedia.page(title, auto_suggest=False).url
                results.append(
                    WikipediaSearchResult(
                        title=title,
                        snippet=summary,
                        url=url,
                    )
                )
            except wikipedia.exceptions.DisambiguationError as e:
                lang_prefix = language if language != "en" else "en"
                results.append(
                    WikipediaSearchResult(
                        title=title,
                        snippet=f"Disambiguation page. Options: {', '.join(e.options[:5])}",
                        url=f"https://{lang_prefix}.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    )
                )
            except wikipedia.exceptions.PageError:
                logger.warning("Wikipedia page not found for title: %s", title)

        logger.info("Wikipedia search complete results=%d", len(results))

        return WikipediaSearchResponse(
            success=True,
            data=WikipediaSearchData(query=query, results=results),
        )
    except Exception as e:
        logger.exception("Wikipedia search failed")
        return WikipediaSearchResponse(
            success=False, error=f"Wikipedia search failed: {str(e)}"
        )


@tool()
async def wikipedia_get_page(
    title: str,
    language: str = "en",
) -> WikipediaGetPageResponse:
    """Retrieve full content of a Wikipedia page by title.

    Args:
        title: The exact title of the Wikipedia page to retrieve.
        language: Wikipedia language code (e.g. "en", "fr", "de", "es", "ja", "zh"). Default is "en".

    Returns:
        Full page content including summary, text, categories, and references.
    """
    try:
        if not title.strip():
            return WikipediaGetPageResponse(
                success=False, error="title must not be empty"
            )

        logger.info("Wikipedia get page title=%s lang=%s", title, language)

        wikipedia.set_lang(language)

        try:
            page = wikipedia.page(title, auto_suggest=False)
        except wikipedia.exceptions.PageError:
            return WikipediaGetPageResponse(
                success=False, error=f"Wikipedia page not found: {title}"
            )
        except wikipedia.exceptions.DisambiguationError as e:
            return WikipediaGetPageResponse(
                success=False,
                error=f"'{title}' is a disambiguation page. Try one of: {', '.join(e.options[:10])}",
            )

        data = WikipediaPageData(
            title=page.title,
            url=page.url,
            summary=page.summary,
            content=page.content,
            categories=list(page.categories),
            references=list(page.references)[:50],
        )

        logger.info(
            "Wikipedia get page complete title=%s content_length=%d",
            page.title,
            len(page.content),
        )

        return WikipediaGetPageResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Wikipedia get page failed")
        return WikipediaGetPageResponse(
            success=False, error=f"Wikipedia get page failed: {str(e)}"
        )


@tool()
async def wikipedia_get_summary(
    title: str,
    sentences: int = 5,
    language: str = "en",
) -> WikipediaGetSummaryResponse:
    """Get a concise summary of a Wikipedia page.

    Returns just the summary/introduction text without the full page content,
    making it faster and more lightweight than wikipedia_get_page.

    Args:
        title: The title of the Wikipedia page.
        sentences: Number of sentences to include in the summary (default 5, max 20).
        language: Wikipedia language code (e.g. "en", "fr", "de", "es", "ja", "zh"). Default is "en".

    Returns:
        A short summary of the page or an error message.
    """
    try:
        if not title.strip():
            return WikipediaGetSummaryResponse(
                success=False, error="title must not be empty"
            )

        sentences = max(1, min(sentences, 20))
        logger.info(
            "Wikipedia get summary title=%s sentences=%d lang=%s",
            title,
            sentences,
            language,
        )

        wikipedia.set_lang(language)

        try:
            summary_text = wikipedia.summary(
                title, sentences=sentences, auto_suggest=False
            )
            page = wikipedia.page(title, auto_suggest=False)
            url = page.url
            resolved_title = page.title
        except wikipedia.exceptions.PageError:
            return WikipediaGetSummaryResponse(
                success=False, error=f"Wikipedia page not found: {title}"
            )
        except wikipedia.exceptions.DisambiguationError as e:
            return WikipediaGetSummaryResponse(
                success=False,
                error=f"'{title}' is a disambiguation page. Try one of: {', '.join(e.options[:10])}",
            )

        return WikipediaGetSummaryResponse(
            success=True,
            data=WikipediaSummaryData(
                title=resolved_title,
                url=url,
                summary=summary_text,
                language=language,
            ),
        )
    except Exception as e:
        logger.exception("Wikipedia get summary failed")
        return WikipediaGetSummaryResponse(
            success=False, error=f"Wikipedia get summary failed: {str(e)}"
        )
