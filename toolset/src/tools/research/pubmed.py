"""PubMed search and article retrieval tools."""

from __future__ import annotations

import logging
import os
from xml.etree import ElementTree

import httpx

from src.humcp.decorator import tool
from src.tools.research.schemas import (
    PubMedArticle,
    PubMedGetArticleData,
    PubMedGetArticleResponse,
    PubMedSearchData,
    PubMedSearchResponse,
)

logger = logging.getLogger("humcp.tools.pubmed")

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def _build_esearch_params(
    query: str,
    max_results: int,
    sort: str | None = None,
    date_type: str | None = None,
    min_date: str | None = None,
    max_date: str | None = None,
    rel_date: int | None = None,
) -> dict:
    """Build query parameters for the E-Search API.

    Args:
        query: Search query string.
        max_results: Maximum number of results.
        sort: Sort order. Options: "most+recent", "pub+date", "journal".
        date_type: Date type for filtering. Options: "pdat" (publication), "edat" (Entrez), "mdat" (modification).
        min_date: Start date in YYYY/MM/DD format (requires max_date).
        max_date: End date in YYYY/MM/DD format (requires min_date).
        rel_date: Relative date - limit to items within last N days.
    """
    params: dict = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "usehistory": "y",
    }
    api_key = os.getenv("NCBI_API_KEY")
    if api_key:
        params["api_key"] = api_key
    if sort:
        params["sort"] = sort
    if date_type:
        params["datetype"] = date_type
    if min_date and max_date:
        params["mindate"] = min_date
        params["maxdate"] = max_date
    if rel_date is not None:
        params["reldate"] = str(rel_date)
    return params


async def _fetch_pubmed_ids(
    query: str,
    max_results: int,
    sort: str | None = None,
    date_type: str | None = None,
    min_date: str | None = None,
    max_date: str | None = None,
    rel_date: int | None = None,
) -> list[str]:
    """Search PubMed and return matching PMIDs."""
    params = _build_esearch_params(
        query,
        max_results,
        sort=sort,
        date_type=date_type,
        min_date=min_date,
        max_date=max_date,
        rel_date=rel_date,
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(ESEARCH_URL, params=params)
        response.raise_for_status()
    root = ElementTree.fromstring(response.content)
    return [
        id_elem.text for id_elem in root.findall(".//Id") if id_elem.text is not None
    ]


async def _fetch_article_details(pmids: list[str]) -> ElementTree.Element:
    """Fetch detailed article XML from PubMed for given PMIDs."""
    params: dict = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }
    api_key = os.getenv("NCBI_API_KEY")
    if api_key:
        params["api_key"] = api_key
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(EFETCH_URL, params=params)
        response.raise_for_status()
    return ElementTree.fromstring(response.content)


def _parse_article(article_elem: ElementTree.Element) -> PubMedArticle:
    """Parse a single PubmedArticle XML element into a PubMedArticle model."""
    # PMID
    pmid_elem = article_elem.find(".//PMID")
    pmid = pmid_elem.text if pmid_elem is not None and pmid_elem.text else ""

    # Title
    title_elem = article_elem.find(".//ArticleTitle")
    title = (
        title_elem.text
        if title_elem is not None and title_elem.text
        else "No title available"
    )

    # Abstract
    abstract_sections = article_elem.findall(".//AbstractText")
    if abstract_sections:
        parts: list[str] = []
        for section in abstract_sections:
            label = section.get("Label", "")
            text = section.text or ""
            if label:
                parts.append(f"{label}: {text}")
            else:
                parts.append(text)
        abstract = "\n\n".join(parts).strip()
    else:
        abstract = "No abstract available"

    # First author
    first_author_elem = article_elem.find(".//AuthorList/Author[1]")
    first_author = "Unknown"
    if first_author_elem is not None:
        last_name = first_author_elem.find("LastName")
        fore_name = first_author_elem.find("ForeName")
        if (
            last_name is not None
            and last_name.text
            and fore_name is not None
            and fore_name.text
        ):
            first_author = f"{last_name.text}, {fore_name.text}"
        elif last_name is not None and last_name.text:
            first_author = last_name.text

    # Journal
    journal_elem = article_elem.find(".//Journal/Title")
    journal = (
        journal_elem.text
        if journal_elem is not None and journal_elem.text
        else "Unknown Journal"
    )

    # Published year
    pub_date = article_elem.find(".//PubDate/Year")
    published = (
        pub_date.text if pub_date is not None and pub_date.text else "No date available"
    )

    # DOI
    doi_elem = article_elem.find(".//ArticleIdList/ArticleId[@IdType='doi']")
    doi = doi_elem.text if doi_elem is not None and doi_elem.text else None

    # PubMed URL
    pubmed_url = (
        f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "No URL available"
    )

    # Full text URL
    pmc_elem = article_elem.find(".//ArticleIdList/ArticleId[@IdType='pmc']")
    full_text_url: str | None = None
    if pmc_elem is not None and pmc_elem.text:
        full_text_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_elem.text}/"
    elif doi:
        full_text_url = f"https://doi.org/{doi}"

    # Keywords
    keywords = [
        kw.text for kw in article_elem.findall(".//KeywordList/Keyword") if kw.text
    ]

    # MeSH terms
    mesh_terms = [
        mesh.text
        for mesh in article_elem.findall(".//MeshHeading/DescriptorName")
        if mesh.text
    ]

    # Publication types
    pub_types = [
        pt.text
        for pt in article_elem.findall(".//PublicationTypeList/PublicationType")
        if pt.text
    ]

    return PubMedArticle(
        pmid=pmid,
        title=title,
        abstract=abstract,
        first_author=first_author,
        journal=journal,
        published=published,
        doi=doi,
        pubmed_url=pubmed_url,
        full_text_url=full_text_url,
        keywords=keywords,
        mesh_terms=mesh_terms,
        publication_types=pub_types,
    )


@tool()
async def pubmed_search(
    query: str,
    max_results: int = 10,
    sort: str | None = None,
    date_type: str | None = None,
    min_date: str | None = None,
    max_date: str | None = None,
    rel_date: int | None = None,
) -> PubMedSearchResponse:
    """Search PubMed for biomedical and life sciences articles.

    Supports NCBI E-utilities search syntax including MeSH terms, boolean
    operators (AND, OR, NOT), and field tags like [Title], [Author], [Journal].

    Args:
        query: The search query for PubMed. Supports field tags like "cancer[Title] AND 2024[Date - Publication]".
        max_results: Maximum number of results to return (default 10, max 200).
        sort: Sort order for results. Options: "most+recent" (default PubMed ordering), "pub+date" (by publication date), "journal" (alphabetical by journal).
        date_type: Date field to filter on. Options: "pdat" (publication date), "edat" (Entrez date), "mdat" (modification date).
        min_date: Start date for date range filter in YYYY/MM/DD, YYYY/MM, or YYYY format. Requires max_date.
        max_date: End date for date range filter in YYYY/MM/DD, YYYY/MM, or YYYY format. Requires min_date.
        rel_date: Limit to items published within the last N days. Overrides min_date/max_date.

    Returns:
        Search results with article metadata including title, abstract, authors, and links.
    """
    try:
        if max_results < 1:
            return PubMedSearchResponse(
                success=False, error="max_results must be at least 1"
            )

        max_results = min(max_results, 200)

        if sort and sort not in {"most+recent", "pub+date", "journal"}:
            return PubMedSearchResponse(
                success=False,
                error=f"Invalid sort '{sort}'. Must be one of: most+recent, pub+date, journal",
            )

        if date_type and date_type not in {"pdat", "edat", "mdat"}:
            return PubMedSearchResponse(
                success=False,
                error=f"Invalid date_type '{date_type}'. Must be one of: pdat, edat, mdat",
            )

        if (min_date and not max_date) or (max_date and not min_date):
            return PubMedSearchResponse(
                success=False,
                error="Both min_date and max_date must be provided together.",
            )

        logger.info(
            "PubMed search query_length=%d max_results=%d sort=%s",
            len(query),
            max_results,
            sort,
        )

        pmids = await _fetch_pubmed_ids(
            query,
            max_results,
            sort=sort,
            date_type=date_type,
            min_date=min_date,
            max_date=max_date,
            rel_date=rel_date,
        )
        if not pmids:
            return PubMedSearchResponse(
                success=True,
                data=PubMedSearchData(query=query, results=[]),
            )

        xml_root = await _fetch_article_details(pmids)
        articles: list[PubMedArticle] = []
        for article_elem in xml_root.findall(".//PubmedArticle"):
            try:
                articles.append(_parse_article(article_elem))
            except Exception as e:
                logger.warning("Skipping article due to parse error: %s", e)

        logger.info("PubMed search complete results=%d", len(articles))

        return PubMedSearchResponse(
            success=True,
            data=PubMedSearchData(query=query, results=articles),
        )
    except Exception as e:
        logger.exception("PubMed search failed")
        return PubMedSearchResponse(
            success=False, error=f"PubMed search failed: {str(e)}"
        )


@tool()
async def pubmed_get_article(
    pmid: str,
) -> PubMedGetArticleResponse:
    """Fetch a single PubMed article by its PMID.

    Args:
        pmid: The PubMed ID of the article to retrieve.

    Returns:
        Full article metadata including title, abstract, authors, and links.
    """
    try:
        if not pmid.strip():
            return PubMedGetArticleResponse(
                success=False, error="pmid must not be empty"
            )

        logger.info("PubMed get article pmid=%s", pmid)

        xml_root = await _fetch_article_details([pmid.strip()])
        article_elems = xml_root.findall(".//PubmedArticle")
        if not article_elems:
            return PubMedGetArticleResponse(
                success=False, error=f"No article found for PMID: {pmid}"
            )

        article = _parse_article(article_elems[0])

        logger.info("PubMed get article complete title=%s", article.title)

        return PubMedGetArticleResponse(
            success=True,
            data=PubMedGetArticleData(article=article),
        )
    except Exception as e:
        logger.exception("PubMed get article failed")
        return PubMedGetArticleResponse(
            success=False, error=f"PubMed get article failed: {str(e)}"
        )
