"""Pydantic output schemas for search tools."""

from pydantic import BaseModel, Field
from src.humcp.schemas import ToolResponse

# =============================================================================
# Tavily Search Data Schemas
# =============================================================================


class TavilySearchResult(BaseModel):
    """A single search result from Tavily."""

    title: str = Field(..., description="Title of the search result")
    url: str = Field(..., description="URL of the search result")
    content: str = Field(..., description="Content snippet from the result")
    score: float = Field(..., description="Relevance score of the result")


class TavilyWebSearchData(BaseModel):
    """Output data for tavily_web_search tool."""

    query: str = Field(..., description="The search query that was executed")
    answer: str | None = Field(None, description="AI-generated answer if available")
    results: list[TavilySearchResult] = Field(..., description="List of search results")


# =============================================================================
# Shared Search Schemas (used by multiple search engines)
# =============================================================================


class SearchResult(BaseModel):
    """A single search result shared across search engines."""

    title: str = Field(..., description="Title of the search result")
    url: str = Field(..., description="URL of the search result")
    snippet: str = Field(
        ..., description="Content snippet or description from the result"
    )
    score: float | None = Field(None, description="Relevance score of the result")


class WebSearchData(BaseModel):
    """Output data for generic web search tools."""

    query: str = Field(..., description="The search query that was executed")
    results: list[SearchResult] = Field(
        default_factory=list, description="List of search results"
    )
    total_results: int | None = Field(
        None, description="Total number of results available"
    )


# =============================================================================
# DuckDuckGo Schemas
# =============================================================================


class DuckDuckGoNewsResult(BaseModel):
    """A single news result from DuckDuckGo."""

    title: str = Field(..., description="Title of the news article")
    url: str = Field(..., description="URL of the news article")
    snippet: str = Field(..., description="Snippet or body of the news article")
    source: str | None = Field(None, description="News source name")
    date: str | None = Field(None, description="Publication date")


class DuckDuckGoNewsData(BaseModel):
    """Output data for duckduckgo_news tool."""

    query: str = Field(..., description="The search query that was executed")
    results: list[DuckDuckGoNewsResult] = Field(
        default_factory=list, description="List of news results"
    )


# =============================================================================
# SerpAPI Schemas
# =============================================================================


class SerpApiSearchData(BaseModel):
    """Output data for serpapi_search tool."""

    query: str = Field(..., description="The search query that was executed")
    results: list[SearchResult] = Field(
        default_factory=list, description="Organic search results"
    )
    knowledge_graph: dict | None = Field(
        None, description="Knowledge graph data if available"
    )
    related_questions: list[dict] | None = Field(
        None, description="Related questions if available"
    )


# =============================================================================
# Exa Schemas
# =============================================================================


class ExaSearchResult(BaseModel):
    """A single search result from Exa."""

    title: str = Field(..., description="Title of the search result")
    url: str = Field(..., description="URL of the search result")
    snippet: str = Field("", description="Text or highlight content from the result")
    highlights: list[str] | None = Field(
        None, description="Key excerpt highlights from the result"
    )
    author: str | None = Field(None, description="Author of the content")
    published_date: str | None = Field(None, description="Publication date")
    score: float | None = Field(None, description="Relevance score")


class ExaSearchData(BaseModel):
    """Output data for exa_search tool."""

    query: str = Field(..., description="The search query that was executed")
    results: list[ExaSearchResult] = Field(
        default_factory=list, description="List of search results"
    )
    autoprompt_string: str | None = Field(
        None, description="Auto-generated prompt string used by Exa"
    )


# =============================================================================
# Seltz Schemas
# =============================================================================


class SeltzSearchResult(BaseModel):
    """A single search result from Seltz."""

    url: str | None = Field(None, description="URL of the document")
    content: str | None = Field(None, description="Document content")
    title: str | None = Field(None, description="Document title")
    score: float | None = Field(None, description="Relevance score")


class SeltzSearchData(BaseModel):
    """Output data for seltz_search tool."""

    query: str = Field(..., description="The search query that was executed")
    results: list[SeltzSearchResult] = Field(
        default_factory=list, description="List of search results"
    )


# =============================================================================
# Valyu Schemas
# =============================================================================


class ValyuSearchResult(BaseModel):
    """A single search result from Valyu."""

    title: str | None = Field(None, description="Title of the result")
    url: str | None = Field(None, description="URL of the result")
    snippet: str | None = Field(None, description="Content snippet from the result")
    source: str | None = Field(None, description="Source name")
    relevance_score: float | None = Field(None, description="Relevance score")


class ValyuSearchData(BaseModel):
    """Output data for valyu_search tool."""

    query: str = Field(..., description="The search query that was executed")
    search_type: str = Field(..., description="Type of search performed")
    results: list[ValyuSearchResult] = Field(
        default_factory=list, description="List of search results"
    )


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class TavilyWebSearchResponse(ToolResponse[TavilyWebSearchData]):
    """Response schema for tavily_web_search tool."""

    pass


class WebSearchResponse(ToolResponse[WebSearchData]):
    """Response schema for generic web search tools (DuckDuckGo, Brave, Serper, SearXNG, Baidu)."""

    pass


class DuckDuckGoNewsResponse(ToolResponse[DuckDuckGoNewsData]):
    """Response schema for duckduckgo_news tool."""

    pass


class SerpApiSearchResponse(ToolResponse[SerpApiSearchData]):
    """Response schema for serpapi_search tool."""

    pass


class ExaSearchResponse(ToolResponse[ExaSearchData]):
    """Response schema for exa_search tool."""

    pass


class SeltzSearchResponse(ToolResponse[SeltzSearchData]):
    """Response schema for seltz_search tool."""

    pass


class ValyuSearchResponse(ToolResponse[ValyuSearchData]):
    """Response schema for valyu_search tool."""

    pass


# =============================================================================
# Tavily Extract Schemas
# =============================================================================


class TavilyExtractResult(BaseModel):
    """A single extract result from Tavily."""

    url: str = Field(..., description="URL that was extracted")
    raw_content: str = Field(..., description="Extracted text content from the URL")


class TavilyExtractData(BaseModel):
    """Output data for tavily_extract tool."""

    results: list[TavilyExtractResult] = Field(
        default_factory=list, description="List of extraction results"
    )
    failed_results: list[dict] | None = Field(
        None, description="URLs that failed to extract"
    )


class TavilyExtractResponse(ToolResponse[TavilyExtractData]):
    """Response schema for tavily_extract tool."""

    pass


# =============================================================================
# Brave News/Image Schemas
# =============================================================================


class BraveNewsResult(BaseModel):
    """A single news result from Brave Search."""

    title: str = Field(..., description="Title of the news article")
    url: str = Field(..., description="URL of the news article")
    description: str = Field("", description="Description snippet")
    age: str | None = Field(
        None, description="Age of the article (e.g., '2 hours ago')"
    )
    source: str | None = Field(None, description="News source name")


class BraveNewsData(BaseModel):
    """Output data for brave_news_search tool."""

    query: str = Field(..., description="The search query")
    results: list[BraveNewsResult] = Field(
        default_factory=list, description="List of news results"
    )


class BraveNewsResponse(ToolResponse[BraveNewsData]):
    """Response schema for brave_news_search tool."""

    pass


class BraveImageResult(BaseModel):
    """A single image result from Brave Search."""

    title: str = Field(..., description="Title of the image")
    url: str = Field(..., description="Page URL containing the image")
    thumbnail_url: str = Field("", description="Thumbnail image URL")
    source: str | None = Field(None, description="Source domain")


class BraveImagesData(BaseModel):
    """Output data for brave_image_search tool."""

    query: str = Field(..., description="The search query")
    results: list[BraveImageResult] = Field(
        default_factory=list, description="List of image results"
    )


class BraveImagesResponse(ToolResponse[BraveImagesData]):
    """Response schema for brave_image_search tool."""

    pass


# =============================================================================
# DuckDuckGo Image Schemas
# =============================================================================


class DuckDuckGoImageResult(BaseModel):
    """A single image result from DuckDuckGo."""

    title: str = Field(..., description="Title of the image")
    url: str = Field(..., description="Page URL containing the image")
    image_url: str = Field(..., description="Direct URL to the image")
    thumbnail_url: str = Field("", description="Thumbnail URL")
    source: str | None = Field(None, description="Source domain")
    width: int | None = Field(None, description="Image width in pixels")
    height: int | None = Field(None, description="Image height in pixels")


class DuckDuckGoImagesData(BaseModel):
    """Output data for duckduckgo_images tool."""

    query: str = Field(..., description="The search query")
    results: list[DuckDuckGoImageResult] = Field(
        default_factory=list, description="List of image results"
    )


class DuckDuckGoImagesResponse(ToolResponse[DuckDuckGoImagesData]):
    """Response schema for duckduckgo_images tool."""

    pass


# =============================================================================
# Exa Find Similar Schemas
# =============================================================================


class ExaFindSimilarData(BaseModel):
    """Output data for exa_find_similar tool."""

    url: str = Field(..., description="The source URL used to find similar pages")
    results: list[ExaSearchResult] = Field(
        default_factory=list, description="List of similar results"
    )


class ExaFindSimilarResponse(ToolResponse[ExaFindSimilarData]):
    """Response schema for exa_find_similar tool."""

    pass


# =============================================================================
# Exa Get Contents Schemas
# =============================================================================


class ExaGetContentsData(BaseModel):
    """Output data for exa_get_contents tool."""

    results: list[ExaSearchResult] = Field(
        default_factory=list, description="Content extracted from the provided URLs"
    )


class ExaGetContentsResponse(ToolResponse[ExaGetContentsData]):
    """Response schema for exa_get_contents tool."""

    pass


# =============================================================================
# Exa Answer Schemas
# =============================================================================


class ExaAnswerData(BaseModel):
    """Output data for exa_answer tool."""

    query: str = Field(..., description="The question that was answered")
    answer: str = Field(..., description="AI-generated answer with citations")
    citations: list[ExaSearchResult] = Field(
        default_factory=list, description="Source citations for the answer"
    )


class ExaAnswerResponse(ToolResponse[ExaAnswerData]):
    """Response schema for exa_answer tool."""

    pass


# =============================================================================
# Serper News/Image Schemas
# =============================================================================


class SerperNewsResult(BaseModel):
    """A single news result from Serper."""

    title: str = Field(..., description="Title of the news article")
    link: str = Field(..., description="URL of the news article")
    snippet: str = Field("", description="Description snippet")
    date: str | None = Field(None, description="Publication date")
    source: str | None = Field(None, description="News source name")


class SerperNewsData(BaseModel):
    """Output data for serper_news_search tool."""

    query: str = Field(..., description="The search query")
    results: list[SerperNewsResult] = Field(
        default_factory=list, description="List of news results"
    )


class SerperNewsResponse(ToolResponse[SerperNewsData]):
    """Response schema for serper_news_search tool."""

    pass


class SerperImageResult(BaseModel):
    """A single image result from Serper."""

    title: str = Field(..., description="Title of the image")
    link: str = Field(..., description="Page URL")
    image_url: str = Field(..., description="Direct image URL")
    source: str | None = Field(None, description="Source domain")


class SerperImagesData(BaseModel):
    """Output data for serper_image_search tool."""

    query: str = Field(..., description="The search query")
    results: list[SerperImageResult] = Field(
        default_factory=list, description="List of image results"
    )


class SerperImagesResponse(ToolResponse[SerperImagesData]):
    """Response schema for serper_image_search tool."""

    pass
