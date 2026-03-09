"""Pydantic output schemas for Google Calendar tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse


class CalendarInfo(BaseModel):
    """Information about a calendar."""

    id: str = Field(..., description="Calendar ID")
    name: str = Field("", description="Calendar name")
    description: str = Field("", description="Calendar description")
    primary: bool = Field(False, description="Whether this is the primary calendar")
    access_role: str = Field("", description="User's access role")


class CalendarEvent(BaseModel):
    """Information about a calendar event."""

    id: str = Field(..., description="Event ID")
    title: str = Field(..., description="Event title")
    description: str = Field("", description="Event description")
    start: str = Field(..., description="Start time (ISO format)")
    end: str = Field(..., description="End time (ISO format)")
    location: str = Field("", description="Event location")
    status: str = Field("", description="Event status")
    html_link: str = Field("", description="Link to event")


class CalendarListData(BaseModel):
    """Output data for google_calendar_list tool."""

    calendars: list[CalendarInfo] = Field(..., description="List of calendars")
    total: int = Field(..., description="Total number of calendars")


class CalendarEventsData(BaseModel):
    """Output data for google_calendar_events tool."""

    events: list[CalendarEvent] = Field(..., description="List of events")
    total: int = Field(..., description="Total number of events")


class CalendarCreateEventData(BaseModel):
    """Output data for google_calendar_create_event tool."""

    id: str = Field(..., description="Created event ID")
    title: str | None = Field(None, description="Event title")
    start: str | None = Field(None, description="Start time")
    end: str | None = Field(None, description="End time")
    html_link: str | None = Field(None, description="Event link")


class CalendarDeleteEventData(BaseModel):
    """Output data for google_calendar_delete_event tool."""

    deleted_event_id: str = Field(..., description="ID of deleted event")


class CalendarQuickAddData(BaseModel):
    """Output data for google_calendar_quick_add tool."""

    id: str = Field(..., description="Created event ID")
    title: str | None = Field(None, description="Event title parsed from text")
    start: str | None = Field(None, description="Start time")
    end: str | None = Field(None, description="End time")
    html_link: str | None = Field(None, description="Event link")


# Calendar Responses
class CalendarListResponse(ToolResponse[CalendarListData]):
    """Response for google_calendar_list tool."""

    pass


class CalendarEventsResponse(ToolResponse[CalendarEventsData]):
    """Response for google_calendar_events tool."""

    pass


class CalendarCreateEventResponse(ToolResponse[CalendarCreateEventData]):
    """Response for google_calendar_create_event tool."""

    pass


class CalendarDeleteEventResponse(ToolResponse[CalendarDeleteEventData]):
    """Response for google_calendar_delete_event tool."""

    pass


class CalendarQuickAddResponse(ToolResponse[CalendarQuickAddData]):
    """Response for google_calendar_quick_add tool."""

    pass
