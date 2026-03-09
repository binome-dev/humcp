"""Pydantic output schemas for research tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# ArXiv Schemas
# =============================================================================


class ArxivArticle(BaseModel):
    """A single article from arXiv search results."""

    title: str = Field(..., description="Title of the article")
    article_id: str = Field(..., description="Short arXiv ID (e.g. '2103.03404v1')")
    entry_id: str = Field(..., description="Full arXiv entry URL")
    authors: list[str] = Field(default_factory=list, description="List of author names")
    primary_category: str = Field(..., description="Primary arXiv category")
    categories: list[str] = Field(
        default_factory=list, description="All arXiv categories"
    )
    published: str | None = Field(None, description="Publication date in ISO format")
    pdf_url: str | None = Field(None, description="URL to the PDF")
    summary: str = Field(..., description="Article abstract/summary")
    comment: str | None = Field(None, description="Author comment if available")


class ArxivSearchData(BaseModel):
    """Output data for arxiv_search tool."""

    query: str = Field(..., description="The search query that was executed")
    results: list[ArxivArticle] = Field(
        default_factory=list, description="List of matching articles"
    )


class ArxivPageContent(BaseModel):
    """Content from a single PDF page."""

    page: int = Field(..., description="Page number (1-indexed)")
    text: str = Field(..., description="Extracted text from the page")


class ArxivPaperContent(BaseModel):
    """Full content of an arXiv paper."""

    title: str = Field(..., description="Title of the paper")
    article_id: str = Field(..., description="Short arXiv ID")
    authors: list[str] = Field(default_factory=list, description="List of author names")
    summary: str = Field(..., description="Paper abstract/summary")
    pages: list[ArxivPageContent] = Field(
        default_factory=list, description="Extracted page content"
    )


class ArxivReadPaperData(BaseModel):
    """Output data for arxiv_read_paper tool."""

    papers: list[ArxivPaperContent] = Field(
        default_factory=list, description="List of papers with extracted content"
    )


class ArxivGetPaperData(BaseModel):
    """Output data for arxiv_get_paper tool."""

    article: ArxivArticle = Field(..., description="The fetched article metadata")


# =============================================================================
# PubMed Schemas
# =============================================================================


class PubMedArticle(BaseModel):
    """A single article from PubMed search results."""

    pmid: str = Field(..., description="PubMed ID")
    title: str = Field(..., description="Article title")
    abstract: str = Field(..., description="Article abstract")
    first_author: str = Field(..., description="First author name")
    journal: str = Field(..., description="Journal name")
    published: str = Field(..., description="Publication year")
    doi: str | None = Field(None, description="Digital Object Identifier")
    pubmed_url: str = Field(..., description="PubMed URL")
    full_text_url: str | None = Field(None, description="Full text URL if available")
    keywords: list[str] = Field(default_factory=list, description="Article keywords")
    mesh_terms: list[str] = Field(default_factory=list, description="MeSH terms")
    publication_types: list[str] = Field(
        default_factory=list, description="Publication types"
    )


class PubMedSearchData(BaseModel):
    """Output data for pubmed_search tool."""

    query: str = Field(..., description="The search query that was executed")
    results: list[PubMedArticle] = Field(
        default_factory=list, description="List of matching articles"
    )


class PubMedGetArticleData(BaseModel):
    """Output data for pubmed_get_article tool."""

    article: PubMedArticle = Field(..., description="The fetched article")


# =============================================================================
# Wikipedia Schemas
# =============================================================================


class WikipediaSearchResult(BaseModel):
    """A single result from Wikipedia search."""

    title: str = Field(..., description="Page title")
    snippet: str = Field(..., description="Short summary or snippet")
    url: str = Field(..., description="URL to the Wikipedia page")


class WikipediaSearchData(BaseModel):
    """Output data for wikipedia_search tool."""

    query: str = Field(..., description="The search query that was executed")
    results: list[WikipediaSearchResult] = Field(
        default_factory=list, description="List of search results"
    )


class WikipediaPageData(BaseModel):
    """Output data for wikipedia_get_page tool."""

    title: str = Field(..., description="Page title")
    url: str = Field(..., description="URL to the Wikipedia page")
    summary: str = Field(..., description="Page summary")
    content: str = Field(..., description="Full page content")
    categories: list[str] = Field(default_factory=list, description="Page categories")
    references: list[str] = Field(
        default_factory=list, description="Page reference URLs"
    )


class WikipediaSummaryData(BaseModel):
    """Output data for wikipedia_get_summary tool."""

    title: str = Field(..., description="Page title")
    url: str = Field(..., description="URL to the Wikipedia page")
    summary: str = Field(..., description="Page summary text")
    language: str = Field("en", description="Wikipedia language code used")


class WikipediaRandomData(BaseModel):
    """Output data for wikipedia_get_random tool."""

    title: str = Field(..., description="Random page title")
    url: str = Field(..., description="URL to the Wikipedia page")
    summary: str = Field(..., description="Page summary text")
    language: str = Field("en", description="Wikipedia language code used")


class ArxivRelatedData(BaseModel):
    """Output data for arxiv_get_related tool."""

    source_paper_id: str = Field(
        ..., description="The source paper ID used to find related papers"
    )
    source_title: str = Field(..., description="Title of the source paper")
    results: list[ArxivArticle] = Field(
        default_factory=list, description="List of related articles"
    )


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class ArxivSearchResponse(ToolResponse[ArxivSearchData]):
    """Response schema for arxiv_search tool."""

    pass


class ArxivReadPaperResponse(ToolResponse[ArxivReadPaperData]):
    """Response schema for arxiv_read_paper tool."""

    pass


class PubMedSearchResponse(ToolResponse[PubMedSearchData]):
    """Response schema for pubmed_search tool."""

    pass


class PubMedGetArticleResponse(ToolResponse[PubMedGetArticleData]):
    """Response schema for pubmed_get_article tool."""

    pass


class WikipediaSearchResponse(ToolResponse[WikipediaSearchData]):
    """Response schema for wikipedia_search tool."""

    pass


class WikipediaGetPageResponse(ToolResponse[WikipediaPageData]):
    """Response schema for wikipedia_get_page tool."""

    pass


class WikipediaGetSummaryResponse(ToolResponse[WikipediaSummaryData]):
    """Response schema for wikipedia_get_summary tool."""

    pass


class ArxivGetPaperResponse(ToolResponse[ArxivGetPaperData]):
    """Response schema for arxiv_get_paper tool."""

    pass


class WikipediaRandomResponse(ToolResponse[WikipediaRandomData]):
    """Response schema for wikipedia_get_random tool."""

    pass


class ArxivRelatedResponse(ToolResponse[ArxivRelatedData]):
    """Response schema for arxiv_get_related tool."""

    pass
