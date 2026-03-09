"""Web scraping and crawling tools using Spider API."""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING

from src.humcp.decorator import tool
from src.tools.web_scraping.schemas import (
    CrawlResponse,
    CrawlResultData,
    ScrapedPageData,
    ScrapeResponse,
    SearchResultItem,
    SpiderLinksData,
    SpiderLinksResponse,
    SpiderSearchData,
    SpiderSearchResponse,
)

if TYPE_CHECKING:
    from spider import Spider as ExternalSpider

logger = logging.getLogger("humcp.tools.spider")


def _get_spider_client() -> ExternalSpider:
    """Create a Spider client instance with lazy import."""
    try:
        from spider import Spider as ExternalSpider
    except ImportError as err:
        raise ImportError(
            "spider-client is required for Spider tools. "
            "Install with: pip install spider-client"
        ) from err

    api_key = os.getenv("SPIDER_API_KEY")
    if not api_key:
        raise ValueError("Spider API not configured. Set SPIDER_API_KEY.")
    return ExternalSpider()


@tool()
async def spider_scrape(url: str) -> ScrapeResponse:
    """Scrape a web page and return its content as markdown using Spider.

    Args:
        url: The URL of the page to scrape.

    Returns:
        Scraped page data with markdown content.
    """
    try:
        if not url:
            return ScrapeResponse(success=False, error="URL is required")

        logger.info("Spider scrape start url=%s", url)

        app = _get_spider_client()
        options = {"return_format": "markdown"}
        results = app.scrape_url(url, options)

        content = ""
        if isinstance(results, list) and len(results) > 0:
            first = results[0]
            content = (
                first.get("content", "") if isinstance(first, dict) else str(first)
            )
        elif isinstance(results, dict):
            content = results.get("content", json.dumps(results))
        else:
            content = str(results)

        data = ScrapedPageData(
            url=url,
            title=None,
            content=content,
            markdown=content,
        )

        logger.info(
            "Spider scrape complete url=%s content_length=%d", url, len(content)
        )
        return ScrapeResponse(success=True, data=data)

    except ValueError as e:
        return ScrapeResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Spider scrape failed")
        return ScrapeResponse(success=False, error=f"Spider scrape failed: {str(e)}")


@tool()
async def spider_crawl(
    url: str,
    limit: int = 10,
    depth: int | None = None,
) -> CrawlResponse:
    """Crawl a website starting from a URL using Spider.

    Discovers and scrapes multiple pages, returning content as markdown.

    Args:
        url: The starting URL to crawl from.
        limit: Maximum number of pages to crawl. Defaults to 10.
        depth: Maximum crawl depth from the starting URL. None means no depth limit.

    Returns:
        Crawl results with data from all discovered pages.
    """
    try:
        if not url:
            return CrawlResponse(success=False, error="URL is required")

        logger.info("Spider crawl start url=%s limit=%d depth=%s", url, limit, depth)

        app = _get_spider_client()
        options: dict = {"return_format": "markdown", "limit": limit}
        if depth is not None:
            options["depth"] = depth

        results = app.crawl_url(url, options)

        pages = []
        if isinstance(results, list):
            for item in results:
                page_content = (
                    item.get("content", "") if isinstance(item, dict) else str(item)
                )
                page_url = item.get("url", url) if isinstance(item, dict) else url
                pages.append(
                    ScrapedPageData(
                        url=page_url,
                        title=None,
                        content=page_content,
                        markdown=page_content,
                    )
                )

        data = CrawlResultData(pages=pages, total_pages=len(pages))

        logger.info("Spider crawl complete url=%s pages=%d", url, len(pages))
        return CrawlResponse(success=True, data=data)

    except ValueError as e:
        return CrawlResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Spider crawl failed")
        return CrawlResponse(success=False, error=f"Spider crawl failed: {str(e)}")


@tool()
async def spider_search(
    query: str,
    limit: int = 5,
) -> SpiderSearchResponse:
    """Search the web using Spider's search endpoint.

    Performs a web search and returns results with content snippets.

    Args:
        query: The search query to execute.
        limit: Maximum number of results to return. Defaults to 5.

    Returns:
        Search results with titles, URLs, and content snippets.
    """
    try:
        if not query:
            return SpiderSearchResponse(success=False, error="Query is required")

        logger.info("Spider search start query=%s limit=%d", query, limit)

        app = _get_spider_client()
        options: dict = {"limit": limit, "return_format": "markdown"}
        results = app.search(query, options)

        items: list[SearchResultItem] = []
        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict):
                    items.append(
                        SearchResultItem(
                            title=item.get("title"),
                            url=item.get("url", ""),
                            content=item.get("content", item.get("description", "")),
                            score=item.get("score"),
                        )
                    )

        data = SpiderSearchData(
            query=query,
            results=items,
            total_results=len(items),
        )

        logger.info("Spider search complete query=%s results=%d", query, len(items))
        return SpiderSearchResponse(success=True, data=data)

    except ValueError as e:
        return SpiderSearchResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Spider search failed")
        return SpiderSearchResponse(
            success=False, error=f"Spider search failed: {str(e)}"
        )


@tool()
async def spider_links(
    url: str,
    limit: int = 100,
) -> SpiderLinksResponse:
    """Extract all links from a web page using Spider.

    Discovers and returns all outbound links found on the specified URL.

    Args:
        url: The URL to extract links from.
        limit: Maximum number of links to return. Defaults to 100.

    Returns:
        List of extracted links from the page.
    """
    try:
        if not url:
            return SpiderLinksResponse(success=False, error="URL is required")

        logger.info("Spider links start url=%s limit=%d", url, limit)

        app = _get_spider_client()
        options: dict = {"limit": limit}
        results = app.links(url, options)

        links: list[str] = []
        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict):
                    page_url = item.get("url", "")
                    if page_url:
                        links.append(page_url)
                elif isinstance(item, str):
                    links.append(item)
        elif isinstance(results, dict):
            raw_links = results.get("links", results.get("urls", []))
            if isinstance(raw_links, list):
                links = [str(link) for link in raw_links]

        data = SpiderLinksData(
            url=url,
            links=links,
            total_links=len(links),
        )

        logger.info("Spider links complete url=%s links=%d", url, len(links))
        return SpiderLinksResponse(success=True, data=data)

    except ValueError as e:
        return SpiderLinksResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Spider links failed")
        return SpiderLinksResponse(
            success=False, error=f"Spider links failed: {str(e)}"
        )
