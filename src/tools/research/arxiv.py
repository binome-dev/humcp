"""arXiv search and paper reading tools."""

from __future__ import annotations

import logging
from pathlib import Path
from tempfile import mkdtemp

from src.humcp.decorator import tool
from src.tools.research.schemas import (
    ArxivArticle,
    ArxivGetPaperData,
    ArxivGetPaperResponse,
    ArxivPageContent,
    ArxivPaperContent,
    ArxivReadPaperData,
    ArxivReadPaperResponse,
    ArxivSearchData,
    ArxivSearchResponse,
)

try:
    import arxiv
except ImportError as err:
    raise ImportError(
        "arxiv is required for arXiv tools. Install with: pip install arxiv"
    ) from err

try:
    from pypdf import PdfReader
except ImportError as err:
    raise ImportError(
        "pypdf is required for arXiv paper reading. Install with: pip install pypdf"
    ) from err

logger = logging.getLogger("humcp.tools.arxiv")


_SORT_BY_MAP = {
    "relevance": arxiv.SortCriterion.Relevance,
    "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
    "submittedDate": arxiv.SortCriterion.SubmittedDate,
}

_SORT_ORDER_MAP = {
    "descending": arxiv.SortOrder.Descending,
    "ascending": arxiv.SortOrder.Ascending,
}


@tool()
async def arxiv_search(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
    sort_order: str = "descending",
) -> ArxivSearchResponse:
    """Search arXiv for academic papers matching a query.

    Supports arXiv query syntax: prefix fields with ti: (title), au: (author),
    abs: (abstract), cat: (category), e.g. "ti:transformer AND cat:cs.CL".

    Args:
        query: The search query to find papers on arXiv. Supports arXiv query syntax.
        max_results: Maximum number of results to return (default 10, max 100).
        sort_by: Sort criterion. One of "relevance", "lastUpdatedDate", "submittedDate". Default is "relevance".
        sort_order: Sort direction. One of "descending", "ascending". Default is "descending".

    Returns:
        Search results with article metadata including title, authors, and abstract.
    """
    try:
        if max_results < 1:
            return ArxivSearchResponse(
                success=False, error="max_results must be at least 1"
            )

        max_results = min(max_results, 100)

        criterion = _SORT_BY_MAP.get(sort_by)
        if criterion is None:
            return ArxivSearchResponse(
                success=False,
                error=f"Invalid sort_by '{sort_by}'. Must be one of: {', '.join(_SORT_BY_MAP.keys())}",
            )

        order = _SORT_ORDER_MAP.get(sort_order)
        if order is None:
            return ArxivSearchResponse(
                success=False,
                error=f"Invalid sort_order '{sort_order}'. Must be one of: {', '.join(_SORT_ORDER_MAP.keys())}",
            )

        logger.info(
            "arXiv search query_length=%d max_results=%d sort_by=%s sort_order=%s",
            len(query),
            max_results,
            sort_by,
            sort_order,
        )

        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=criterion,
            sort_order=order,
        )

        articles: list[ArxivArticle] = []
        for result in client.results(search):
            try:
                article = ArxivArticle(
                    title=result.title,
                    article_id=result.get_short_id(),
                    entry_id=result.entry_id,
                    authors=[author.name for author in result.authors],
                    primary_category=result.primary_category,
                    categories=list(result.categories),
                    published=result.published.isoformat()
                    if result.published
                    else None,
                    pdf_url=result.pdf_url,
                    summary=result.summary,
                    comment=result.comment,
                )
                articles.append(article)
            except Exception as e:
                logger.warning("Skipping article due to parse error: %s", e)

        logger.info("arXiv search complete results=%d", len(articles))

        return ArxivSearchResponse(
            success=True,
            data=ArxivSearchData(query=query, results=articles),
        )
    except Exception as e:
        logger.exception("arXiv search failed")
        return ArxivSearchResponse(
            success=False, error=f"arXiv search failed: {str(e)}"
        )


@tool()
async def arxiv_read_paper(
    paper_ids: list[str],
    pages_to_read: int | None = None,
) -> ArxivReadPaperResponse:
    """Download and read arXiv papers by their IDs.

    Args:
        paper_ids: List of arXiv paper IDs (e.g. ['2103.03404v1', '2301.07041v2']).
        pages_to_read: Maximum number of pages to read per paper. None reads all pages.

    Returns:
        Extracted text content from the requested papers.
    """
    try:
        if not paper_ids:
            return ArxivReadPaperResponse(
                success=False, error="paper_ids must not be empty"
            )

        logger.info("arXiv read papers=%s pages_limit=%s", paper_ids, pages_to_read)

        download_dir = Path(mkdtemp(prefix="arxiv_pdfs_"))
        client = arxiv.Client()

        papers: list[ArxivPaperContent] = []
        for result in client.results(search=arxiv.Search(id_list=paper_ids)):
            try:
                pages_content: list[ArxivPageContent] = []

                if result.pdf_url:
                    logger.info("Downloading PDF: %s", result.pdf_url)
                    pdf_path = result.download_pdf(dirpath=str(download_dir))
                    pdf_reader = PdfReader(pdf_path)

                    for page_number, page in enumerate(pdf_reader.pages, start=1):
                        if pages_to_read is not None and page_number > pages_to_read:
                            break
                        text = page.extract_text() or ""
                        pages_content.append(
                            ArxivPageContent(page=page_number, text=text)
                        )

                paper = ArxivPaperContent(
                    title=result.title,
                    article_id=result.get_short_id(),
                    authors=[author.name for author in result.authors],
                    summary=result.summary,
                    pages=pages_content,
                )
                papers.append(paper)
            except Exception as e:
                logger.warning(
                    "Skipping paper %s due to error: %s", result.get_short_id(), e
                )

        logger.info("arXiv read complete papers=%d", len(papers))

        return ArxivReadPaperResponse(
            success=True,
            data=ArxivReadPaperData(papers=papers),
        )
    except Exception as e:
        logger.exception("arXiv read papers failed")
        return ArxivReadPaperResponse(
            success=False, error=f"arXiv read papers failed: {str(e)}"
        )


@tool()
async def arxiv_get_paper(
    paper_id: str,
) -> ArxivGetPaperResponse:
    """Get metadata for a single arXiv paper by its ID.

    Returns the paper's title, authors, abstract, categories, and PDF URL
    without downloading the full PDF.

    Args:
        paper_id: The arXiv paper ID (e.g. "2103.03404" or "2103.03404v1").

    Returns:
        Paper metadata or an error message.
    """
    try:
        if not paper_id.strip():
            return ArxivGetPaperResponse(
                success=False, error="paper_id must not be empty"
            )

        logger.info("arXiv get paper id=%s", paper_id)

        client = arxiv.Client()
        results = list(client.results(arxiv.Search(id_list=[paper_id.strip()])))

        if not results:
            return ArxivGetPaperResponse(
                success=False, error=f"Paper '{paper_id}' not found on arXiv."
            )

        result = results[0]
        article = ArxivArticle(
            title=result.title,
            article_id=result.get_short_id(),
            entry_id=result.entry_id,
            authors=[author.name for author in result.authors],
            primary_category=result.primary_category,
            categories=list(result.categories),
            published=result.published.isoformat() if result.published else None,
            pdf_url=result.pdf_url,
            summary=result.summary,
            comment=result.comment,
        )

        logger.info("arXiv get paper complete title=%s", article.title)
        return ArxivGetPaperResponse(
            success=True,
            data=ArxivGetPaperData(article=article),
        )
    except Exception as e:
        logger.exception("arXiv get paper failed")
        return ArxivGetPaperResponse(
            success=False, error=f"arXiv get paper failed: {str(e)}"
        )
