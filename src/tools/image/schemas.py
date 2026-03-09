"""Pydantic output schemas for image processing tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# OCR Tool Schemas
# =============================================================================


class ImageExtractTextData(BaseModel):
    """Output data for image_extract_text tool."""

    markdown: str = Field(..., description="Extracted text in markdown format")
    message: str | None = Field(
        None, description="Additional message (e.g., 'No text found in image')"
    )


class ImageExtractTextResponse(ToolResponse[ImageExtractTextData]):
    """Response schema for image_extract_text tool."""

    pass
