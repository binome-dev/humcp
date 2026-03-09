"""Web scraping tool using Browserbase cloud browser infrastructure."""

from __future__ import annotations

import logging
import re

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.web_scraping.schemas import ScrapedPageData, ScrapeResponse

logger = logging.getLogger("humcp.tools.browserbase")


def _extract_text_from_html(html: str) -> str:
    """Extract visible text content from HTML."""
    cleaned = re.sub(
        r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
    )
    cleaned = re.sub(
        r"<style[^>]*>.*?</style>", "", cleaned, flags=re.DOTALL | re.IGNORECASE
    )
    cleaned = re.sub(r"<!--.*?-->", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = cleaned.replace("&nbsp;", " ")
    cleaned = cleaned.replace("&amp;", "&")
    cleaned = cleaned.replace("&lt;", "<")
    cleaned = cleaned.replace("&gt;", ">")
    cleaned = cleaned.replace("&quot;", '"')
    cleaned = cleaned.replace("&#39;", "'")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


@tool()
async def browserbase_scrape(
    url: str,
    max_content_length: int = 100000,
) -> ScrapeResponse:
    """Scrape a web page using Browserbase cloud browser.

    Uses Browserbase to spin up a cloud-hosted browser, navigate to the URL,
    and extract the page content. Good for JavaScript-heavy pages.
    Requires BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID.

    Args:
        url: The URL to scrape.
        max_content_length: Maximum content length in characters. Defaults to 100000.

    Returns:
        Scraped page data with extracted text content.
    """
    try:
        try:
            from browserbase import Browserbase
        except ImportError as err:
            raise ImportError(
                "browserbase is required for Browserbase tools. "
                "Install with: pip install browserbase"
            ) from err

        api_key = await resolve_credential("BROWSERBASE_API_KEY")
        project_id = await resolve_credential("BROWSERBASE_PROJECT_ID")

        if not api_key:
            return ScrapeResponse(
                success=False,
                error="Browserbase API not configured. Set BROWSERBASE_API_KEY.",
            )
        if not project_id:
            return ScrapeResponse(
                success=False,
                error="Browserbase project not configured. Set BROWSERBASE_PROJECT_ID.",
            )
        if not url:
            return ScrapeResponse(success=False, error="URL is required")

        logger.info("Browserbase scrape start url=%s", url)

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as err:
            raise ImportError(
                "playwright is required. Install with: pip install playwright && playwright install"
            ) from err

        app = Browserbase(api_key=api_key)
        session = app.sessions.create(project_id=project_id)
        connect_url = session.connect_url if session else ""

        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(connect_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            page.goto(url, wait_until="networkidle")
            title = page.title()
            raw_content = page.content()
            browser.close()

        content = _extract_text_from_html(raw_content)

        if max_content_length and len(content) > max_content_length:
            content = (
                content[:max_content_length]
                + f"\n\n[Content truncated. Original length: {len(content)} characters.]"
            )

        data = ScrapedPageData(
            url=url,
            title=title if title else None,
            content=content,
            markdown=None,
        )

        logger.info(
            "Browserbase scrape complete url=%s content_length=%d",
            url,
            len(content),
        )
        return ScrapeResponse(success=True, data=data)

    except ImportError:
        raise
    except Exception as e:
        logger.exception("Browserbase scrape failed")
        return ScrapeResponse(
            success=False, error=f"Browserbase scrape failed: {str(e)}"
        )
