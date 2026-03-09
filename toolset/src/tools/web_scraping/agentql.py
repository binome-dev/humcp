"""Web scraping tool using AgentQL for structured data extraction."""

from __future__ import annotations

import json
import logging
import os

from src.humcp.decorator import tool
from src.tools.web_scraping.schemas import ScrapedPageData, ScrapeResponse

logger = logging.getLogger("humcp.tools.agentql")

_DEFAULT_QUERY = """
{
    text_content[]
}
"""


@tool()
async def agentql_query(
    url: str,
    query: str | None = None,
) -> ScrapeResponse:
    """Scrape a web page using AgentQL to extract structured data.

    Uses AgentQL's query language with a headless browser to extract
    specific data from web pages. Requires AGENTQL_API_KEY.

    Args:
        url: The URL of the website to scrape.
        query: AgentQL query string for extraction. If not provided, extracts all text content.

    Returns:
        Scraped page data with extracted content.
    """
    try:
        try:
            import agentql
            from playwright.sync_api import sync_playwright
        except ImportError as err:
            raise ImportError(
                "agentql is required for AgentQL tools. "
                "Install with: pip install agentql"
            ) from err

        api_key = os.getenv("AGENTQL_API_KEY")
        if not api_key:
            return ScrapeResponse(
                success=False,
                error="AgentQL API not configured. Set AGENTQL_API_KEY.",
            )

        if not url:
            return ScrapeResponse(success=False, error="URL is required")

        logger.info("AgentQL query start url=%s", url)

        agentql_query_str = query if query else _DEFAULT_QUERY

        with (
            sync_playwright() as playwright,
            playwright.chromium.launch(headless=True) as browser,
        ):
            page = agentql.wrap(browser.new_page())
            page.goto(url)

            response = page.query_data(agentql_query_str)

            if not response:
                return ScrapeResponse(
                    success=False, error="No data returned from AgentQL query"
                )

            if isinstance(response, dict) and "text_content" in response:
                text_items = [
                    item
                    for item in response["text_content"]
                    if item and str(item).strip()
                ]
                content = " ".join(list(set(text_items)))
            elif isinstance(response, dict):
                content = json.dumps(response, indent=2)
            else:
                content = str(response)

        data = ScrapedPageData(
            url=url,
            title=None,
            content=content,
            markdown=None,
            metadata={"query": agentql_query_str.strip()},
        )

        logger.info(
            "AgentQL query complete url=%s content_length=%d", url, len(content)
        )
        return ScrapeResponse(success=True, data=data)

    except ImportError:
        raise
    except Exception as e:
        logger.exception("AgentQL query failed")
        return ScrapeResponse(success=False, error=f"AgentQL query failed: {str(e)}")
