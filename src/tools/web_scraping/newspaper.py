"""Article extraction tool using newspaper4k (free, no API key required)."""

from __future__ import annotations

import logging

from src.humcp.decorator import tool
from src.tools.web_scraping.schemas import ScrapedPageData, ScrapeResponse

logger = logging.getLogger("humcp.tools.newspaper")


@tool()
async def newspaper_extract(
    url: str,
    max_length: int | None = None,
    include_nlp: bool = False,
) -> ScrapeResponse:
    """Extract article content from a URL using newspaper4k.

    Parses news articles and blog posts to extract title, authors,
    publish date, and main text content. Free with no API key required.

    Args:
        url: The URL of the article to extract.
        max_length: Optional maximum character length for the article text.
        include_nlp: Whether to run NLP for keyword and summary extraction. Defaults to False.

    Returns:
        Scraped page data with article text, title, top image, and metadata.
    """
    if not url:
        return ScrapeResponse(success=False, error="URL is required")

    try:
        try:
            import newspaper
        except ImportError as err:
            raise ImportError(
                "newspaper4k is required for newspaper tools. "
                "Install with: pip install newspaper4k lxml_html_clean"
            ) from err

        logger.info("Newspaper extract start url=%s include_nlp=%s", url, include_nlp)

        article = newspaper.article(url)

        if not article or not article.text:
            return ScrapeResponse(
                success=False,
                error=f"Could not extract article content from {url}",
            )

        text = article.text
        if max_length and len(text) > max_length:
            text = text[:max_length]

        metadata: dict = {}
        if article.authors:
            metadata["authors"] = article.authors
        try:
            if article.publish_date:
                metadata["publish_date"] = article.publish_date.isoformat()
        except Exception:
            pass
        if article.summary:
            metadata["summary"] = article.summary

        top_image = getattr(article, "top_image", None) or getattr(
            article, "top_img", None
        )
        if top_image:
            metadata["top_image"] = top_image

        if include_nlp:
            try:
                if hasattr(article, "nlp") and callable(article.nlp):
                    article.nlp()
                keywords = getattr(article, "keywords", None)
                if keywords:
                    metadata["keywords"] = keywords
                nlp_summary = getattr(article, "summary", None)
                if nlp_summary:
                    metadata["summary"] = nlp_summary
            except Exception as nlp_err:
                logger.warning("NLP extraction failed: %s", nlp_err)

        data = ScrapedPageData(
            url=url,
            title=article.title if article.title else None,
            content=text,
            markdown=None,
            metadata=metadata if metadata else None,
        )

        logger.info(
            "Newspaper extract complete url=%s content_length=%d", url, len(text)
        )
        return ScrapeResponse(success=True, data=data)

    except ImportError:
        raise
    except Exception as e:
        logger.exception("Newspaper extract failed")
        return ScrapeResponse(
            success=False, error=f"Newspaper extract failed: {str(e)}"
        )
