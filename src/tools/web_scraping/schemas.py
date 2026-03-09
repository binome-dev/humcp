"""Pydantic output schemas for web scraping tools."""

from typing import Any

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# Shared Data Models
# =============================================================================


class ScrapedPageData(BaseModel):
    """Data from a single scraped web page."""

    url: str = Field(..., description="URL of the scraped page")
    title: str | None = Field(None, description="Page title")
    content: str = Field(..., description="Extracted text content")
    markdown: str | None = Field(None, description="Content in markdown format")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class CrawlResultData(BaseModel):
    """Data from a multi-page crawl operation."""

    pages: list[ScrapedPageData] = Field(..., description="List of scraped pages")
    total_pages: int = Field(..., description="Total number of pages crawled")


# =============================================================================
# Structured Extraction Data Models
# =============================================================================


class StructuredScrapeData(BaseModel):
    """Data from an AI-powered structured extraction."""

    url: str = Field(..., description="URL that was scraped")
    prompt: str = Field(..., description="Extraction prompt used")
    result: dict[str, Any] | str = Field(
        ..., description="Structured data extracted by the LLM"
    )


class SearchResultItem(BaseModel):
    """A single search result item."""

    title: str | None = Field(None, description="Title of the result")
    url: str = Field(..., description="URL of the result")
    content: str = Field(..., description="Content snippet or description")
    score: float | None = Field(None, description="Relevance score")


class SearchResultData(BaseModel):
    """Data from a search operation."""

    query: str = Field(..., description="The search query that was executed")
    results: list[SearchResultItem] = Field(..., description="List of search results")


class ActorRunData(BaseModel):
    """Data from an Apify actor run."""

    actor_id: str = Field(..., description="ID of the actor that was run")
    results: list[dict[str, Any]] = Field(..., description="Results from the actor run")
    total_items: int = Field(..., description="Total number of result items")


# =============================================================================
# Map / URL Discovery Data Models
# =============================================================================


class MapResultData(BaseModel):
    """Data from a URL discovery / map operation."""

    base_url: str = Field(..., description="The base URL that was mapped")
    urls: list[str] = Field(..., description="Discovered URLs")
    total_urls: int = Field(..., description="Total number of discovered URLs")


# =============================================================================
# Firecrawl Search Data Models
# =============================================================================


class FirecrawlSearchData(BaseModel):
    """Data from a Firecrawl search operation."""

    query: str = Field(..., description="The search query that was executed")
    results: list[ScrapedPageData] = Field(
        ..., description="Search results with full page content"
    )
    total_results: int = Field(..., description="Total number of results returned")


# =============================================================================
# Spider Search Data Models
# =============================================================================


class SpiderSearchData(BaseModel):
    """Data from a Spider search operation."""

    query: str = Field(..., description="The search query that was executed")
    results: list[SearchResultItem] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results returned")


# =============================================================================
# Spider Links Data Models
# =============================================================================


class SpiderLinksData(BaseModel):
    """Data from a Spider link extraction operation."""

    url: str = Field(..., description="The URL that was scanned for links")
    links: list[str] = Field(..., description="Extracted links")
    total_links: int = Field(..., description="Total number of links found")


# =============================================================================
# Crawl4AI Links Data Models
# =============================================================================


class LinkItem(BaseModel):
    """A single extracted link with optional metadata."""

    href: str = Field(..., description="The link URL")
    text: str | None = Field(None, description="The anchor text of the link")
    is_external: bool = Field(
        False, description="Whether the link points to an external domain"
    )


class Crawl4aiLinksData(BaseModel):
    """Data from a Crawl4AI link extraction operation."""

    url: str = Field(..., description="The URL that was scanned for links")
    links: list[LinkItem] = Field(..., description="Extracted links with metadata")
    total_links: int = Field(..., description="Total number of links found")
    internal_count: int = Field(0, description="Number of internal links")
    external_count: int = Field(0, description="Number of external links")


# =============================================================================
# ScrapeGraph Search Data Models
# =============================================================================


class ScrapegraphSearchData(BaseModel):
    """Data from a ScrapeGraph search operation."""

    query: str = Field(..., description="The search query that was executed")
    result: dict[str, Any] | str = Field(
        ..., description="AI-structured search results"
    )


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class ScrapeResponse(ToolResponse[ScrapedPageData]):
    """Response schema for single-page scrape tools."""

    pass


class CrawlResponse(ToolResponse[CrawlResultData]):
    """Response schema for multi-page crawl tools."""

    pass


class StructuredScrapeResponse(ToolResponse[StructuredScrapeData]):
    """Response schema for AI-powered structured extraction tools."""

    pass


class SearchResponse(ToolResponse[SearchResultData]):
    """Response schema for search tools."""

    pass


class ActorRunResponse(ToolResponse[ActorRunData]):
    """Response schema for Apify actor run tools."""

    pass


class MapResponse(ToolResponse[MapResultData]):
    """Response schema for URL discovery / map tools."""

    pass


class FirecrawlSearchResponse(ToolResponse[FirecrawlSearchData]):
    """Response schema for Firecrawl search tools."""

    pass


class SpiderSearchResponse(ToolResponse[SpiderSearchData]):
    """Response schema for Spider search tools."""

    pass


class SpiderLinksResponse(ToolResponse[SpiderLinksData]):
    """Response schema for Spider link extraction tools."""

    pass


class Crawl4aiLinksResponse(ToolResponse[Crawl4aiLinksData]):
    """Response schema for Crawl4AI link extraction tools."""

    pass


class ScrapegraphSearchResponse(ToolResponse[ScrapegraphSearchData]):
    """Response schema for ScrapeGraph search tools."""

    pass
