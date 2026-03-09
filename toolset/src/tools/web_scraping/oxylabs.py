"""Web scraping tool using Oxylabs Realtime API."""

from __future__ import annotations

import json
import logging
import os

from src.humcp.decorator import tool
from src.tools.web_scraping.schemas import ScrapedPageData, ScrapeResponse

logger = logging.getLogger("humcp.tools.oxylabs")


@tool()
async def oxylabs_scrape(
    url: str,
    source: str = "universal",
    render_javascript: bool = False,
) -> ScrapeResponse:
    """Scrape a web page using Oxylabs Realtime API.

    Uses Oxylabs' proxy infrastructure to scrape web pages reliably.
    Supports multiple source types for specialized scraping.
    Requires OXYLABS_USERNAME and OXYLABS_PASSWORD.

    Args:
        url: The URL to scrape.
        source: Scraping source type - 'universal', 'google', 'amazon', etc. Defaults to 'universal'.
        render_javascript: Whether to render JavaScript before extraction. Defaults to False.

    Returns:
        Scraped page data with extracted content.
    """
    try:
        try:
            from oxylabs import RealtimeClient
        except ImportError as err:
            raise ImportError(
                "Oxylabs SDK is required for Oxylabs tools. "
                "Install with: pip install oxylabs"
            ) from err

        username = os.getenv("OXYLABS_USERNAME")
        password = os.getenv("OXYLABS_PASSWORD")

        if not username or not password:
            return ScrapeResponse(
                success=False,
                error="Oxylabs credentials not configured. Set OXYLABS_USERNAME and OXYLABS_PASSWORD.",
            )

        if not url:
            return ScrapeResponse(success=False, error="URL is required")

        logger.info("Oxylabs scrape start url=%s source=%s", url, source)

        client = RealtimeClient(username, password)

        render_param = None
        if render_javascript:
            try:
                from oxylabs.utils.types import render

                render_param = render.HTML
            except ImportError:
                logger.warning(
                    "Could not import render types; proceeding without JS rendering"
                )

        response = client.universal.scrape_url(url=url, render=render_param, parse=True)

        content = ""
        title = None
        metadata: dict = {"source": source, "javascript_rendered": render_javascript}

        if response.results and len(response.results) > 0:
            result = response.results[0]
            raw_content = result.content

            if raw_content:
                if isinstance(raw_content, dict):
                    content = json.dumps(raw_content)
                    title = raw_content.get("title")
                else:
                    content = str(raw_content)

            status_code = getattr(result, "status_code", None)
            if status_code:
                metadata["status_code"] = status_code

        data = ScrapedPageData(
            url=url,
            title=title,
            content=content,
            markdown=None,
            metadata=metadata,
        )

        logger.info(
            "Oxylabs scrape complete url=%s content_length=%d", url, len(content)
        )
        return ScrapeResponse(success=True, data=data)

    except ImportError:
        raise
    except Exception as e:
        logger.exception("Oxylabs scrape failed")
        return ScrapeResponse(success=False, error=f"Oxylabs scrape failed: {str(e)}")
