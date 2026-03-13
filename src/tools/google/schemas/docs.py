"""Pydantic output schemas for Google Docs tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse


class DocInfo(BaseModel):
    """Basic document information."""

    id: str = Field(..., description="Document ID")
    name: str = Field(..., description="Document name")
    modified: str = Field("", description="Last modified date")
    web_link: str = Field("", description="Web view link")


class DocsSearchData(BaseModel):
    """Output data for google_docs_search tool."""

    documents: list[DocInfo] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")


class DocsGetContentData(BaseModel):
    """Output data for google_docs_get_content tool."""

    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document text content")
    revision_id: str = Field("", description="Document revision ID")


class DocsCreateData(BaseModel):
    """Output data for google_docs_create tool."""

    id: str = Field(..., description="Created document ID")
    title: str = Field(..., description="Document title")
    web_link: str = Field(..., description="Document link")


class DocsAppendTextData(BaseModel):
    """Output data for google_docs_append_text tool."""

    updated: bool = Field(..., description="Whether update succeeded")
    document_id: str = Field(..., description="Document ID")


class DocsFindReplaceData(BaseModel):
    """Output data for google_docs_find_replace tool."""

    document_id: str = Field(..., description="Document ID")
    find_text: str = Field(..., description="Text that was searched")
    replace_text: str = Field(..., description="Replacement text")
    replacements: int = Field(..., description="Number of replacements made")


class DocsListInFolderData(BaseModel):
    """Output data for google_docs_list_in_folder tool."""

    documents: list[DocInfo] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")


# Docs Responses
class DocsSearchResponse(ToolResponse[DocsSearchData]):
    """Response for google_docs_search tool."""

    pass


class DocsGetContentResponse(ToolResponse[DocsGetContentData]):
    """Response for google_docs_get_content tool."""

    pass


class DocsCreateResponse(ToolResponse[DocsCreateData]):
    """Response for google_docs_create tool."""

    pass


class DocsAppendTextResponse(ToolResponse[DocsAppendTextData]):
    """Response for google_docs_append_text tool."""

    pass


class DocsFindReplaceResponse(ToolResponse[DocsFindReplaceData]):
    """Response for google_docs_find_replace tool."""

    pass


class DocsListInFolderResponse(ToolResponse[DocsListInFolderData]):
    """Response for google_docs_list_in_folder tool."""

    pass
