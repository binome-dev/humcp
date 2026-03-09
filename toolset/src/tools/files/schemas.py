"""Pydantic output schemas for file conversion tools."""

from pydantic import BaseModel, Field
from src.humcp.schemas import ToolResponse

# =============================================================================
# PDF to Markdown Schemas
# =============================================================================


class ConvertToMarkdownData(BaseModel):
    """Output data for convert_to_markdown tool."""

    markdown: str = Field(..., description="The converted markdown content")


class ConvertToMarkdownResponse(ToolResponse[ConvertToMarkdownData]):
    """Response schema for convert_to_markdown tool."""

    pass


# =============================================================================
# Markdown Table Extraction Schemas
# =============================================================================


class ExtractedTable(BaseModel):
    """Information about a single extracted table."""

    index: int = Field(..., description="Table index in the document (0-based)")
    rows: int = Field(..., description="Number of rows in the table")
    columns: int = Field(..., description="Number of columns in the table")
    csv: str = Field(..., description="Table content as CSV string")


class MarkdownExtractTablesData(BaseModel):
    """Output data for markdown_extract_tables tool."""

    tables: list[ExtractedTable] = Field(..., description="List of extracted tables")
    count: int = Field(..., description="Number of tables extracted")
    message: str | None = Field(
        None, description="Additional message (e.g., no tables found)"
    )


class MarkdownExtractTablesResponse(ToolResponse[MarkdownExtractTablesData]):
    """Response schema for markdown_extract_tables tool."""

    pass
