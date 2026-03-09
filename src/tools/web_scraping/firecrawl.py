"""Web scraping and crawling tools using Firecrawl API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.web_scraping.schemas import (
    CrawlResponse,
    CrawlResultData,
    FirecrawlSearchData,
    FirecrawlSearchResponse,
    MapResponse,
    MapResultData,
    ScrapedPageData,
    ScrapeResponse,
)

if TYPE_CHECKING:
    from firecrawl import FirecrawlApp

logger = logging.getLogger("humcp.tools.firecrawl")


def _get_firecrawl_app(api_key: str) -> FirecrawlApp:
    """Create a FirecrawlApp instance with lazy import."""
    try:
        from firecrawl import FirecrawlApp
    except ImportError as err:
        raise ImportError(
            "firecrawl-py is required for Firecrawl tools. "
            "Install with: pip install firecrawl-py"
        ) from err

    return FirecrawlApp(api_key=api_key)


@tool()
async def firecrawl_scrape(
    url: str,
    formats: list[str] | None = None,
) -> ScrapeResponse:
    """Scrape a single web page using Firecrawl.

    Extracts clean content from a URL with optional format selection.

    Args:
        url: The URL to scrape.
        formats: Output formats (e.g., ['markdown', 'html']). Defaults to markdown.

    Returns:
        Scraped page data with content and metadata.
    """
    try:
        if not url:
            return ScrapeResponse(success=False, error="URL is required")

        logger.info("Firecrawl scrape start url=%s", url)

        api_key = await resolve_credential("FIRECRAWL_API_KEY")
        if not api_key:
            return ScrapeResponse(
                success=False,
                error="Firecrawl API not configured. Set FIRECRAWL_API_KEY.",
            )

        app = _get_firecrawl_app(api_key)
        params = {}
        if formats:
            params["formats"] = formats

        result = app.scrape(url, **params)
        result_dict = result.model_dump() if hasattr(result, "model_dump") else result

        content = result_dict.get("markdown", result_dict.get("html", ""))
        markdown = result_dict.get("markdown")
        title = result_dict.get("metadata", {}).get("title")
        metadata = result_dict.get("metadata")

        data = ScrapedPageData(
            url=url,
            title=title,
            content=content,
            markdown=markdown,
            metadata=metadata,
        )

        logger.info("Firecrawl scrape complete url=%s", url)
        return ScrapeResponse(success=True, data=data)

    except ValueError as e:
        return ScrapeResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Firecrawl scrape failed")
        return ScrapeResponse(success=False, error=f"Firecrawl scrape failed: {str(e)}")


@tool()
async def firecrawl_crawl(
    url: str,
    limit: int = 10,
    formats: list[str] | None = None,
) -> CrawlResponse:
    """Crawl a website starting from a URL using Firecrawl.

    Discovers and scrapes multiple pages from a website up to the specified limit.

    Args:
        url: The starting URL to crawl from.
        limit: Maximum number of pages to crawl. Defaults to 10.
        formats: Output formats for each page (e.g., ['markdown']). Defaults to markdown.

    Returns:
        Crawl results with data from all discovered pages.
    """
    try:
        if not url:
            return CrawlResponse(success=False, error="URL is required")

        logger.info("Firecrawl crawl start url=%s limit=%d", url, limit)

        api_key = await resolve_credential("FIRECRAWL_API_KEY")
        if not api_key:
            return CrawlResponse(
                success=False,
                error="Firecrawl API not configured. Set FIRECRAWL_API_KEY.",
            )

        app = _get_firecrawl_app(api_key)
        params: dict = {"limit": limit, "poll_interval": 30}
        if formats:
            try:
                from firecrawl.types import ScrapeOptions
            except ImportError:
                pass
            else:
                params["scrape_options"] = ScrapeOptions(formats=formats)

        result = app.crawl(url, **params)
        result_dict = result.model_dump() if hasattr(result, "model_dump") else result

        pages = []
        crawl_data = (
            result_dict.get("data", []) if isinstance(result_dict, dict) else []
        )
        for page in crawl_data:
            content = page.get("markdown", page.get("html", ""))
            pages.append(
                ScrapedPageData(
                    url=page.get("url", url),
                    title=page.get("metadata", {}).get("title"),
                    content=content,
                    markdown=page.get("markdown"),
                    metadata=page.get("metadata"),
                )
            )

        data = CrawlResultData(pages=pages, total_pages=len(pages))

        logger.info("Firecrawl crawl complete url=%s pages=%d", url, len(pages))
        return CrawlResponse(success=True, data=data)

    except ValueError as e:
        return CrawlResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Firecrawl crawl failed")
        return CrawlResponse(success=False, error=f"Firecrawl crawl failed: {str(e)}")


@tool()
async def firecrawl_map(
    url: str,
    limit: int = 100,
    search: str | None = None,
) -> MapResponse:
    """Discover URLs on a website using Firecrawl's map endpoint.

    Quickly maps all accessible URLs on a website without scraping content.
    Useful for site discovery and planning targeted scrapes.

    Args:
        url: The base URL to map.
        limit: Maximum number of URLs to discover. Defaults to 100.
        search: Optional search term to filter discovered URLs.

    Returns:
        List of discovered URLs on the website.
    """
    try:
        if not url:
            return MapResponse(success=False, error="URL is required")

        logger.info("Firecrawl map start url=%s limit=%d", url, limit)

        api_key = await resolve_credential("FIRECRAWL_API_KEY")
        if not api_key:
            return MapResponse(
                success=False,
                error="Firecrawl API not configured. Set FIRECRAWL_API_KEY.",
            )

        app = _get_firecrawl_app(api_key)
        params: dict = {"limit": limit}
        if search:
            params["search"] = search

        result = app.map(url, **params)

        urls: list[str] = []
        if isinstance(result, list):
            urls = [str(u) for u in result]
        elif isinstance(result, dict):
            raw = result.get("urls", result.get("links", result.get("data", [])))
            if isinstance(raw, list):
                urls = [str(u) for u in raw]
        elif hasattr(result, "model_dump"):
            result_dict = result.model_dump()
            raw = result_dict.get("urls", result_dict.get("links", []))
            if isinstance(raw, list):
                urls = [str(u) for u in raw]

        data = MapResultData(
            base_url=url,
            urls=urls,
            total_urls=len(urls),
        )

        logger.info("Firecrawl map complete url=%s urls=%d", url, len(urls))
        return MapResponse(success=True, data=data)

    except ValueError as e:
        return MapResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Firecrawl map failed")
        return MapResponse(success=False, error=f"Firecrawl map failed: {str(e)}")


@tool()
async def firecrawl_search(
    query: str,
    limit: int = 5,
    formats: list[str] | None = None,
) -> FirecrawlSearchResponse:
    """Search the web and retrieve full page content using Firecrawl.

    Performs a web search and returns scraped content for each result,
    combining search with scraping in a single operation.

    Args:
        query: The search query to execute.
        limit: Maximum number of results to return. Defaults to 5.
        formats: Output formats for each result (e.g., ['markdown']). Defaults to markdown.

    Returns:
        Search results with full scraped page content.
    """
    try:
        if not query:
            return FirecrawlSearchResponse(success=False, error="Query is required")

        logger.info("Firecrawl search start query=%s limit=%d", query, limit)

        api_key = await resolve_credential("FIRECRAWL_API_KEY")
        if not api_key:
            return FirecrawlSearchResponse(
                success=False,
                error="Firecrawl API not configured. Set FIRECRAWL_API_KEY.",
            )

        app = _get_firecrawl_app(api_key)
        params: dict = {"limit": limit}
        if formats:
            params["scrape_options"] = {"formats": formats}

        result = app.search(query, **params)

        results: list[ScrapedPageData] = []
        raw_data: list = []

        if isinstance(result, list):
            raw_data = result
        elif isinstance(result, dict):
            raw_data = result.get("data", result.get("results", []))
        elif hasattr(result, "model_dump"):
            result_dict = result.model_dump()
            raw_data = result_dict.get("data", result_dict.get("results", []))
        elif hasattr(result, "data"):
            raw_data = result.data if isinstance(result.data, list) else []

        for item in raw_data:
            item_dict = item.model_dump() if hasattr(item, "model_dump") else item
            if not isinstance(item_dict, dict):
                continue
            content = item_dict.get("markdown", item_dict.get("content", ""))
            results.append(
                ScrapedPageData(
                    url=item_dict.get("url", ""),
                    title=item_dict.get("metadata", {}).get(
                        "title", item_dict.get("title")
                    ),
                    content=content,
                    markdown=item_dict.get("markdown"),
                    metadata=item_dict.get("metadata"),
                )
            )

        data = FirecrawlSearchData(
            query=query,
            results=results,
            total_results=len(results),
        )

        logger.info(
            "Firecrawl search complete query=%s results=%d", query, len(results)
        )
        return FirecrawlSearchResponse(success=True, data=data)

    except ValueError as e:
        return FirecrawlSearchResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Firecrawl search failed")
        return FirecrawlSearchResponse(
            success=False, error=f"Firecrawl search failed: {str(e)}"
        )
