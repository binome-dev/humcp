"""Web content extraction tool using trafilatura (free, no API key required)."""

from __future__ import annotations

import logging

from src.humcp.decorator import tool
from src.tools.web_scraping.schemas import ScrapedPageData, ScrapeResponse

logger = logging.getLogger("humcp.tools.trafilatura")


@tool()
async def trafilatura_extract(
    url: str,
    include_comments: bool = False,
    output_format: str = "txt",
    include_links: bool = False,
    include_images: bool = False,
    favor_precision: bool = False,
) -> ScrapeResponse:
    """Extract main text content from a web page using trafilatura.

    Trafilatura is optimized for extracting the main content from web pages,
    filtering out boilerplate, navigation, and other non-content elements.
    Free to use with no API key required.

    Args:
        url: The URL to extract content from.
        include_comments: Whether to include comments in the extraction. Defaults to False.
        output_format: Output format: 'txt', 'markdown', 'xml', 'json'. Defaults to 'txt'.
        include_links: Whether to keep links/references in the extracted text. Defaults to False.
        include_images: Whether to include image references in the output. Defaults to False.
        favor_precision: Whether to favor precision over recall in extraction (stricter filtering). Defaults to False.

    Returns:
        Scraped page data with extracted content.
    """
    if not url:
        return ScrapeResponse(success=False, error="URL is required")

    try:
        try:
            from trafilatura import extract, extract_metadata, fetch_url
            from trafilatura.meta import reset_caches
        except ImportError as err:
            raise ImportError(
                "trafilatura is required for trafilatura tools. "
                "Install with: pip install trafilatura"
            ) from err

        logger.info("Trafilatura extract start url=%s", url)

        html_content = fetch_url(url)
        if not html_content:
            return ScrapeResponse(
                success=False,
                error=f"Could not fetch content from URL: {url}",
            )

        result = extract(
            html_content,
            url=url,
            include_comments=include_comments,
            include_tables=True,
            include_links=include_links,
            include_images=include_images,
            favor_precision=favor_precision,
            output_format=output_format,
        )

        if result is None:
            reset_caches()
            return ScrapeResponse(
                success=False,
                error=f"Could not extract readable content from URL: {url}",
            )

        # Extract metadata
        metadata_doc = extract_metadata(html_content, default_url=url)
        metadata = None
        title = None
        if metadata_doc:
            metadata_dict = metadata_doc.as_dict()
            title = metadata_dict.get("title")
            metadata = {
                k: v for k, v in metadata_dict.items() if v is not None and k != "title"
            }

        reset_caches()

        markdown = result if output_format == "markdown" else None

        data = ScrapedPageData(
            url=url,
            title=title,
            content=result,
            markdown=markdown,
            metadata=metadata if metadata else None,
        )

        logger.info(
            "Trafilatura extract complete url=%s content_length=%d",
            url,
            len(result),
        )
        return ScrapeResponse(success=True, data=data)

    except ImportError:
        raise
    except Exception as e:
        logger.exception("Trafilatura extract failed")
        return ScrapeResponse(
            success=False, error=f"Trafilatura extract failed: {str(e)}"
        )
