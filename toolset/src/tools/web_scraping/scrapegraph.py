"""AI-powered web scraping tool using ScrapeGraphAI."""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING

from src.humcp.decorator import tool
from src.tools.web_scraping.schemas import (
    ScrapedPageData,
    ScrapegraphSearchData,
    ScrapegraphSearchResponse,
    ScrapeResponse,
    StructuredScrapeData,
    StructuredScrapeResponse,
)

if TYPE_CHECKING:
    from scrapegraph_py import Client

logger = logging.getLogger("humcp.tools.scrapegraph")


def _get_scrapegraph_client() -> Client:
    """Create a ScrapeGraph client instance with lazy import."""
    try:
        from scrapegraph_py import Client
    except ImportError as err:
        raise ImportError(
            "scrapegraph-py is required for ScrapeGraph tools. "
            "Install with: pip install scrapegraph-py"
        ) from err

    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        raise ValueError("ScrapeGraph API not configured. Set SGAI_API_KEY.")
    return Client(api_key=api_key)


@tool()
async def scrapegraph_scrape(
    url: str,
    prompt: str,
) -> StructuredScrapeResponse:
    """Extract structured data from a web page using AI with ScrapeGraphAI.

    Uses an LLM to intelligently extract specific information from a web page
    based on a natural language prompt. Requires SGAI_API_KEY.

    Args:
        url: The URL to scrape.
        prompt: Natural language description of what data to extract.

    Returns:
        Structured extraction results based on the prompt.
    """
    try:
        if not url:
            return StructuredScrapeResponse(success=False, error="URL is required")
        if not prompt:
            return StructuredScrapeResponse(success=False, error="Prompt is required")

        logger.info("ScrapeGraph scrape start url=%s", url)

        client = _get_scrapegraph_client()
        response = client.smartscraper(website_url=url, user_prompt=prompt)

        result = response.get("result", response)
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except (json.JSONDecodeError, ValueError):
                pass

        data = StructuredScrapeData(
            url=url,
            prompt=prompt,
            result=result,
        )

        logger.info("ScrapeGraph scrape complete url=%s", url)
        return StructuredScrapeResponse(success=True, data=data)

    except ValueError as e:
        return StructuredScrapeResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("ScrapeGraph scrape failed")
        return StructuredScrapeResponse(
            success=False, error=f"ScrapeGraph scrape failed: {str(e)}"
        )


@tool()
async def scrapegraph_markdownify(
    url: str,
) -> ScrapeResponse:
    """Convert a web page to clean markdown using ScrapeGraphAI.

    Fetches a web page and converts it to well-formatted markdown.
    Requires SGAI_API_KEY.

    Args:
        url: The URL to convert to markdown.

    Returns:
        Scraped page data with markdown content.
    """
    try:
        if not url:
            return ScrapeResponse(success=False, error="URL is required")

        logger.info("ScrapeGraph markdownify start url=%s", url)

        client = _get_scrapegraph_client()
        response = client.markdownify(website_url=url)

        markdown_content = response.get("result", "")

        data = ScrapedPageData(
            url=url,
            title=None,
            content=markdown_content,
            markdown=markdown_content,
        )

        logger.info(
            "ScrapeGraph markdownify complete url=%s content_length=%d",
            url,
            len(markdown_content),
        )
        return ScrapeResponse(success=True, data=data)

    except ValueError as e:
        return ScrapeResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("ScrapeGraph markdownify failed")
        return ScrapeResponse(
            success=False, error=f"ScrapeGraph markdownify failed: {str(e)}"
        )


@tool()
async def scrapegraph_search(
    query: str,
) -> ScrapegraphSearchResponse:
    """Search the web using ScrapeGraphAI's searchscraper.

    Performs an AI-powered web search that returns structured results
    based on the query. Requires SGAI_API_KEY.

    Args:
        query: The search query or natural language question to answer.

    Returns:
        AI-structured search results.
    """
    try:
        if not query:
            return ScrapegraphSearchResponse(success=False, error="Query is required")

        logger.info("ScrapeGraph search start query=%s", query)

        client = _get_scrapegraph_client()
        response = client.searchscraper(user_prompt=query)

        result = response.get("result", response)
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except (json.JSONDecodeError, ValueError):
                pass

        data = ScrapegraphSearchData(
            query=query,
            result=result,
        )

        logger.info("ScrapeGraph search complete query=%s", query)
        return ScrapegraphSearchResponse(success=True, data=data)

    except ValueError as e:
        return ScrapegraphSearchResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("ScrapeGraph search failed")
        return ScrapegraphSearchResponse(
            success=False, error=f"ScrapeGraph search failed: {str(e)}"
        )
