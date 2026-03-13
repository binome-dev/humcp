"""Web scraping tool using Crawl4AI (free, no API key required)."""

from __future__ import annotations

import logging

from src.humcp.decorator import tool
from src.tools.web_scraping.schemas import (
    Crawl4aiLinksData,
    Crawl4aiLinksResponse,
    LinkItem,
    ScrapedPageData,
    ScrapeResponse,
)

logger = logging.getLogger("humcp.tools.crawl4ai")


@tool()
async def crawl4ai_scrape(
    url: str,
    extract_markdown: bool = True,
    max_length: int = 5000,
) -> ScrapeResponse:
    """Scrape a web page and extract its content using Crawl4AI.

    Uses a headless browser to render the page, then extracts clean text
    or markdown. Free to use with no API key required.

    Args:
        url: The URL of the page to scrape.
        extract_markdown: Whether to return content as markdown. Defaults to True.
        max_length: Maximum character length of returned content. Defaults to 5000.

    Returns:
        Scraped page data including content and optional markdown.
    """
    if not url:
        return ScrapeResponse(success=False, error="URL is required")

    try:
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        except ImportError as err:
            raise ImportError(
                "crawl4ai is required for Crawl4AI tools. "
                "Install with: pip install crawl4ai"
            ) from err

        logger.info("Crawl4AI scrape start url=%s", url)

        browser_config = BrowserConfig(headless=True, verbose=False)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                page_timeout=60000,
                wait_until="domcontentloaded",
                cache_mode="bypass",
                verbose=False,
            )
            result = await crawler.arun(url=url, config=config)

            if not result:
                return ScrapeResponse(
                    success=False, error="No content returned from page"
                )

            # Extract markdown content
            markdown_content = None
            text_content = ""

            if hasattr(result, "fit_markdown") and result.fit_markdown:
                markdown_content = result.fit_markdown
            elif hasattr(result, "markdown") and result.markdown:
                if hasattr(result.markdown, "raw_markdown"):
                    markdown_content = result.markdown.raw_markdown
                else:
                    markdown_content = str(result.markdown)

            if hasattr(result, "text") and result.text:
                text_content = result.text
            elif markdown_content:
                text_content = markdown_content

            if not text_content and not markdown_content:
                return ScrapeResponse(
                    success=False,
                    error="Could not extract readable content from page",
                )

            # Truncate if needed
            if max_length and len(text_content) > max_length:
                text_content = text_content[:max_length] + "..."
            if markdown_content and max_length and len(markdown_content) > max_length:
                markdown_content = markdown_content[:max_length] + "..."

            title = None
            if hasattr(result, "title"):
                title = result.title

            data = ScrapedPageData(
                url=url,
                title=title,
                content=text_content,
                markdown=markdown_content if extract_markdown else None,
            )

            logger.info(
                "Crawl4AI scrape complete url=%s content_length=%d",
                url,
                len(text_content),
            )
            return ScrapeResponse(success=True, data=data)

    except ImportError:
        raise
    except Exception as e:
        logger.exception("Crawl4AI scrape failed")
        return ScrapeResponse(success=False, error=f"Crawl4AI scrape failed: {str(e)}")


def _parse_domain(url: str) -> str:
    """Extract the domain from a URL for internal/external classification."""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        return netloc.removeprefix("www.")
    except Exception:
        return ""


@tool()
async def crawl4ai_extract_links(
    url: str,
    include_external: bool = True,
    max_links: int = 200,
) -> Crawl4aiLinksResponse:
    """Extract all links from a web page using Crawl4AI.

    Uses a headless browser to render the page, then extracts all anchor
    links with their text and classifies them as internal or external.
    Free to use with no API key required.

    Args:
        url: The URL of the page to extract links from.
        include_external: Whether to include external links. Defaults to True.
        max_links: Maximum number of links to return. Defaults to 200.

    Returns:
        Extracted links with metadata including internal/external classification.
    """
    if not url:
        return Crawl4aiLinksResponse(success=False, error="URL is required")

    try:
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        except ImportError as err:
            raise ImportError(
                "crawl4ai is required for Crawl4AI tools. "
                "Install with: pip install crawl4ai"
            ) from err

        logger.info("Crawl4AI extract_links start url=%s", url)

        source_domain = _parse_domain(url)
        browser_config = BrowserConfig(headless=True, verbose=False)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                page_timeout=60000,
                wait_until="domcontentloaded",
                cache_mode="bypass",
                verbose=False,
            )
            result = await crawler.arun(url=url, config=config)

            if not result:
                return Crawl4aiLinksResponse(
                    success=False, error="No content returned from page"
                )

            raw_links: list[dict] = []
            if hasattr(result, "links") and result.links:
                links_data = result.links
                if isinstance(links_data, dict):
                    for link_list in links_data.values():
                        if isinstance(link_list, list):
                            raw_links.extend(link_list)
                elif isinstance(links_data, list):
                    raw_links = links_data

            link_items: list[LinkItem] = []
            internal_count = 0
            external_count = 0

            seen_hrefs: set[str] = set()

            for raw_link in raw_links:
                if len(link_items) >= max_links:
                    break

                href = ""
                text = None

                if isinstance(raw_link, dict):
                    href = raw_link.get("href", raw_link.get("url", ""))
                    text = raw_link.get("text", raw_link.get("anchor", None))
                elif isinstance(raw_link, str):
                    href = raw_link
                else:
                    continue

                if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                    continue

                if href in seen_hrefs:
                    continue
                seen_hrefs.add(href)

                link_domain = _parse_domain(href)
                is_external = bool(
                    link_domain and source_domain and link_domain != source_domain
                )

                if not include_external and is_external:
                    continue

                if is_external:
                    external_count += 1
                else:
                    internal_count += 1

                link_items.append(
                    LinkItem(
                        href=href,
                        text=text if text else None,
                        is_external=is_external,
                    )
                )

            data = Crawl4aiLinksData(
                url=url,
                links=link_items,
                total_links=len(link_items),
                internal_count=internal_count,
                external_count=external_count,
            )

            logger.info(
                "Crawl4AI extract_links complete url=%s total=%d internal=%d external=%d",
                url,
                len(link_items),
                internal_count,
                external_count,
            )
            return Crawl4aiLinksResponse(success=True, data=data)

    except ImportError:
        raise
    except Exception as e:
        logger.exception("Crawl4AI extract_links failed")
        return Crawl4aiLinksResponse(
            success=False, error=f"Crawl4AI extract_links failed: {str(e)}"
        )
