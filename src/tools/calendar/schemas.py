"""Pydantic output schemas for calendar tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# Cal.com Schemas
# =============================================================================


class CalcomBooking(BaseModel):
    """A single booking from Cal.com."""

    uid: str = Field(..., description="Unique booking identifier")
    title: str = Field(..., description="Booking title")
    start_time: str = Field(..., description="Booking start time in ISO 8601 format")
    end_time: str | None = Field(
        None, description="Booking end time in ISO 8601 format"
    )
    status: str = Field(
        ..., description="Booking status (accepted, pending, cancelled)"
    )
    attendee_name: str | None = Field(None, description="Primary attendee name")
    attendee_email: str | None = Field(None, description="Primary attendee email")
    location: str | None = Field(None, description="Meeting location or video link")


class CalcomListBookingsData(BaseModel):
    """Output data for calcom_list_bookings tool."""

    bookings: list[CalcomBooking] = Field(
        default_factory=list, description="List of bookings"
    )
    status_filter: str | None = Field(None, description="Status filter applied")


class CalcomCreateBookingData(BaseModel):
    """Output data for calcom_create_booking tool."""

    uid: str = Field(..., description="Unique booking identifier")
    start_time: str = Field(..., description="Booking start time")
    event_type_id: int = Field(..., description="Event type ID")
    attendee_name: str = Field(..., description="Attendee name")
    attendee_email: str = Field(..., description="Attendee email")


class CalcomCancelBookingData(BaseModel):
    """Output data for calcom_cancel_booking tool."""

    uid: str = Field(..., description="Booking UID that was cancelled")
    message: str = Field(..., description="Cancellation confirmation message")


class CalcomRescheduleBookingData(BaseModel):
    """Output data for calcom_reschedule_booking tool."""

    uid: str = Field(..., description="New booking UID after reschedule")
    start_time: str = Field(..., description="New start time")
    message: str = Field(..., description="Reschedule confirmation message")


class CalcomAvailabilitySlot(BaseModel):
    """A single availability slot from Cal.com."""

    time: str = Field(..., description="Available time slot in ISO 8601 format")


class CalcomAvailabilityData(BaseModel):
    """Output data for calcom_get_availability tool."""

    event_type_id: int = Field(..., description="Event type ID")
    date_from: str = Field(..., description="Start date of availability range")
    date_to: str = Field(..., description="End date of availability range")
    slots: list[CalcomAvailabilitySlot] = Field(
        default_factory=list, description="List of available time slots"
    )


class CalcomEventType(BaseModel):
    """A Cal.com event type."""

    id: int = Field(..., description="Event type ID")
    title: str = Field(..., description="Event type title")
    slug: str | None = Field(None, description="URL slug for the event type")
    description: str | None = Field(None, description="Event type description")
    length: int | None = Field(None, description="Duration in minutes")
    hidden: bool | None = Field(None, description="Whether the event type is hidden")


class CalcomListEventTypesData(BaseModel):
    """Output data for calcom_list_event_types tool."""

    event_types: list[CalcomEventType] = Field(
        default_factory=list, description="List of event types"
    )
    count: int = Field(..., description="Total number of event types")


# =============================================================================
# Zoom Schemas
# =============================================================================


class ZoomMeeting(BaseModel):
    """A single Zoom meeting."""

    meeting_id: str = Field(..., description="Zoom meeting ID")
    topic: str = Field(..., description="Meeting topic/title")
    start_time: str | None = Field(
        None, description="Meeting start time in ISO 8601 format"
    )
    duration: int | None = Field(None, description="Meeting duration in minutes")
    timezone: str | None = Field(None, description="Meeting timezone (IANA format)")
    join_url: str | None = Field(None, description="URL to join the meeting")
    status: str | None = Field(None, description="Meeting status (waiting, started)")
    type: int | None = Field(
        None,
        description="Meeting type (1=instant, 2=scheduled, 3=recurring no fixed time, 8=recurring fixed time)",
    )


class ZoomCreateMeetingData(BaseModel):
    """Output data for zoom_create_meeting tool."""

    meeting_id: str = Field(..., description="Created meeting ID")
    topic: str = Field(..., description="Meeting topic")
    start_time: str = Field(..., description="Meeting start time")
    duration: int = Field(..., description="Meeting duration in minutes")
    timezone: str = Field(..., description="Meeting timezone")
    join_url: str = Field(..., description="URL to join the meeting")
    password: str | None = Field(None, description="Meeting password if set")


class ZoomListMeetingsData(BaseModel):
    """Output data for zoom_list_meetings tool."""

    meetings: list[ZoomMeeting] = Field(
        default_factory=list, description="List of meetings"
    )
    total_records: int = Field(0, description="Total number of meetings")


class ZoomGetMeetingData(BaseModel):
    """Output data for zoom_get_meeting tool."""

    meeting: ZoomMeeting = Field(..., description="Meeting details")


class ZoomDeleteMeetingData(BaseModel):
    """Output data for zoom_delete_meeting tool."""

    meeting_id: str = Field(..., description="ID of the deleted meeting")
    message: str = Field(..., description="Deletion confirmation message")


class ZoomUpdateMeetingData(BaseModel):
    """Output data for zoom_update_meeting tool."""

    meeting_id: str = Field(..., description="ID of the updated meeting")
    message: str = Field(..., description="Update confirmation message")


class ZoomMeetingParticipant(BaseModel):
    """A participant in a Zoom meeting."""

    name: str = Field(..., description="Participant name")
    email: str | None = Field(None, description="Participant email")
    join_time: str | None = Field(None, description="Time the participant joined")
    leave_time: str | None = Field(None, description="Time the participant left")
    duration: int | None = Field(None, description="Duration in the meeting in seconds")


class ZoomListParticipantsData(BaseModel):
    """Output data for zoom_list_meeting_participants tool."""

    meeting_id: str = Field(..., description="Meeting ID")
    participants: list[ZoomMeetingParticipant] = Field(
        default_factory=list, description="List of participants"
    )
    total_records: int = Field(0, description="Total number of participants")


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class CalcomListBookingsResponse(ToolResponse[CalcomListBookingsData]):
    """Response schema for calcom_list_bookings tool."""

    pass


class CalcomCreateBookingResponse(ToolResponse[CalcomCreateBookingData]):
    """Response schema for calcom_create_booking tool."""

    pass


class CalcomCancelBookingResponse(ToolResponse[CalcomCancelBookingData]):
    """Response schema for calcom_cancel_booking tool."""

    pass


class CalcomRescheduleBookingResponse(ToolResponse[CalcomRescheduleBookingData]):
    """Response schema for calcom_reschedule_booking tool."""

    pass


class CalcomAvailabilityResponse(ToolResponse[CalcomAvailabilityData]):
    """Response schema for calcom_get_availability tool."""

    pass


class CalcomListEventTypesResponse(ToolResponse[CalcomListEventTypesData]):
    """Response schema for calcom_list_event_types tool."""

    pass


class ZoomCreateMeetingResponse(ToolResponse[ZoomCreateMeetingData]):
    """Response schema for zoom_create_meeting tool."""

    pass


class ZoomListMeetingsResponse(ToolResponse[ZoomListMeetingsData]):
    """Response schema for zoom_list_meetings tool."""

    pass


class ZoomGetMeetingResponse(ToolResponse[ZoomGetMeetingData]):
    """Response schema for zoom_get_meeting tool."""

    pass


class ZoomDeleteMeetingResponse(ToolResponse[ZoomDeleteMeetingData]):
    """Response schema for zoom_delete_meeting tool."""

    pass


class ZoomUpdateMeetingResponse(ToolResponse[ZoomUpdateMeetingData]):
    """Response schema for zoom_update_meeting tool."""

    pass


class ZoomListParticipantsResponse(ToolResponse[ZoomListParticipantsData]):
    """Response schema for zoom_list_meeting_participants tool."""

    pass
