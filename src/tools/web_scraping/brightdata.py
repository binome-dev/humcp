"""Web scraping tool using BrightData Web Unlocker API."""

from __future__ import annotations

import json
import logging
import os

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.web_scraping.schemas import ScrapedPageData, ScrapeResponse

logger = logging.getLogger("humcp.tools.brightdata")

_BRIGHTDATA_ENDPOINT = "https://api.brightdata.com/request"


@tool()
async def brightdata_scrape(
    url: str,
    country: str | None = None,
) -> ScrapeResponse:
    """Scrape a web page as markdown using BrightData Web Unlocker.

    Uses BrightData's proxy and unlocker infrastructure to bypass restrictions
    and return page content as clean markdown. Requires BRIGHTDATA_API_KEY.

    Args:
        url: The URL to scrape.
        country: Two-letter country code for geolocation (e.g., 'us', 'gb', 'de'). Routes request through the specified country.

    Returns:
        Scraped page data with markdown content.
    """
    try:
        api_key = await resolve_credential("BRIGHTDATA_API_KEY")
        if not api_key:
            return ScrapeResponse(
                success=False,
                error="BrightData API not configured. Set BRIGHTDATA_API_KEY.",
            )

        if not url:
            return ScrapeResponse(success=False, error="URL is required")

        logger.info("BrightData scrape start url=%s country=%s", url, country)

        zone = os.getenv("BRIGHTDATA_WEB_UNLOCKER_ZONE", "unblocker")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload: dict = {
            "url": url,
            "zone": zone,
            "format": "raw",
            "data_format": "markdown",
        }
        if country:
            payload["country"] = country.lower()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                _BRIGHTDATA_ENDPOINT,
                headers=headers,
                content=json.dumps(payload),
                timeout=120.0,
            )
            response.raise_for_status()

        content = response.text

        data = ScrapedPageData(
            url=url,
            title=None,
            content=content,
            markdown=content,
        )

        logger.info(
            "BrightData scrape complete url=%s content_length=%d",
            url,
            len(content),
        )
        return ScrapeResponse(success=True, data=data)

    except Exception as e:
        logger.exception("BrightData scrape failed")
        return ScrapeResponse(
            success=False, error=f"BrightData scrape failed: {str(e)}"
        )
