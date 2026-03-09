"""Pydantic output schemas for Google Slides tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse


class PresentationInfo(BaseModel):
    """Basic presentation information."""

    id: str = Field(..., description="Presentation ID")
    name: str = Field(..., description="Presentation name")
    modified: str = Field("", description="Last modified date")
    web_link: str = Field("", description="Web view link")


class SlideElement(BaseModel):
    """Element in a slide."""

    type: str = Field(..., description="Element type")
    content: str = Field("", description="Element content")


class SlideInfo(BaseModel):
    """Information about a slide."""

    id: str = Field(..., description="Slide ID")
    elements: list[SlideElement] = Field(
        default_factory=list, description="Slide elements"
    )


class PresentationDetailed(BaseModel):
    """Detailed presentation information."""

    id: str = Field(..., description="Presentation ID")
    title: str = Field("", description="Presentation title")
    slide_count: int = Field(0, description="Number of slides")
    slides: list[SlideInfo] = Field(default_factory=list, description="Slide info")
    width: float = Field(0, description="Page width")
    height: float = Field(0, description="Page height")


class PresentationCreated(BaseModel):
    """Information about a created presentation."""

    id: str = Field(..., description="Presentation ID")
    title: str = Field("", description="Presentation title")
    slide_count: int = Field(0, description="Number of slides")
    web_link: str = Field("", description="Web link")


class SlideAdded(BaseModel):
    """Information about an added slide."""

    slide_id: str | None = Field(None, description="New slide ID")
    presentation_id: str = Field(..., description="Presentation ID")
    layout: str = Field("", description="Slide layout")


class TextAdded(BaseModel):
    """Information about added text."""

    shape_id: str = Field(..., description="Shape ID")
    slide_id: str = Field(..., description="Slide ID")
    text: str = Field("", description="Text content")


class SlideThumbnail(BaseModel):
    """Slide thumbnail information."""

    slide_id: str = Field(..., description="Slide ID")
    content_url: str = Field("", description="Thumbnail URL")
    width: int = Field(0, description="Thumbnail width")
    height: int = Field(0, description="Thumbnail height")


class SlidesListData(BaseModel):
    """Output data for google_slides_list_presentations tool."""

    presentations: list[PresentationInfo] = Field(
        ..., description="List of presentations"
    )
    total: int = Field(..., description="Total number of presentations")


# Slides Responses
class SlidesListPresentationsResponse(ToolResponse[SlidesListData]):
    """Response for google_slides_list_presentations tool."""

    pass


class SlidesGetPresentationResponse(ToolResponse[PresentationDetailed]):
    """Response for google_slides_get_presentation tool."""

    pass


class SlidesCreatePresentationResponse(ToolResponse[PresentationCreated]):
    """Response for google_slides_create_presentation tool."""

    pass


class SlidesAddSlideResponse(ToolResponse[SlideAdded]):
    """Response for google_slides_add_slide tool."""

    pass


class SlidesAddTextResponse(ToolResponse[TextAdded]):
    """Response for google_slides_add_text tool."""

    pass


class SlidesGetThumbnailResponse(ToolResponse[SlideThumbnail]):
    """Response for google_slides_get_thumbnail tool."""

    pass
