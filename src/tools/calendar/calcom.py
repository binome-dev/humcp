"""Cal.com booking and scheduling management tools.

Wraps the Cal.com Platform API v2 for managing bookings, availability, and
event types.  Supports listing, creating, cancelling, and rescheduling bookings,
checking availability, and listing event types.

Environment variables:
    CALCOM_API_KEY: Bearer token for Cal.com API v2 authentication.
    CALCOM_BASE_URL: Base URL override (default: https://api.cal.com/v2).
"""

from __future__ import annotations

import logging
import os

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.calendar.schemas import (
    CalcomAvailabilityData,
    CalcomAvailabilityResponse,
    CalcomAvailabilitySlot,
    CalcomBooking,
    CalcomCancelBookingData,
    CalcomCancelBookingResponse,
    CalcomCreateBookingData,
    CalcomCreateBookingResponse,
    CalcomEventType,
    CalcomListBookingsData,
    CalcomListBookingsResponse,
    CalcomListEventTypesData,
    CalcomListEventTypesResponse,
    CalcomRescheduleBookingData,
    CalcomRescheduleBookingResponse,
)

logger = logging.getLogger("humcp.tools.calcom")

CALCOM_DEFAULT_BASE_URL = "https://api.cal.com/v2"
CALCOM_API_VERSION = "2024-08-13"


def _get_calcom_config(api_key: str | None) -> tuple[str | None, str]:
    """Resolve Cal.com API key and base URL.

    Args:
        api_key: Resolved Cal.com API key.

    Returns:
        Tuple of (api_key, base_url).
    """
    base_url = os.getenv("CALCOM_BASE_URL", CALCOM_DEFAULT_BASE_URL)
    return api_key, base_url


def _calcom_headers(api_key: str) -> dict[str, str]:
    """Build Cal.com API request headers with versioning."""
    return {
        "Authorization": f"Bearer {api_key}",
        "cal-api-version": CALCOM_API_VERSION,
        "Content-Type": "application/json",
    }


@tool()
async def calcom_list_bookings(
    status: str = "upcoming",
) -> CalcomListBookingsResponse:
    """List bookings from Cal.com filtered by status.

    Retrieves bookings for the authenticated user with the given status filter.

    Args:
        status: Booking status filter. Options: 'upcoming' (default), 'past',
                'cancelled', 'recurring'.

    Returns:
        List of bookings with details including title, times, status, and attendee.
    """
    try:
        api_key_val = await resolve_credential("CALCOM_API_KEY")
        if not api_key_val:
            return CalcomListBookingsResponse(
                success=False, error="Cal.com API not configured. Set CALCOM_API_KEY."
            )

        api_key, base_url = _get_calcom_config(api_key_val)

        logger.info("Cal.com list bookings start status=%s", status)

        url = f"{base_url}/bookings"
        params = {"status": status}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                url, headers=_calcom_headers(api_key), params=params
            )
            response.raise_for_status()

        bookings_data = response.json().get("data", [])

        bookings = [
            CalcomBooking(
                uid=booking["uid"],
                title=booking.get("title", ""),
                start_time=booking.get("start", ""),
                end_time=booking.get("end"),
                status=booking.get("status", ""),
                attendee_name=booking.get("attendees", [{}])[0].get("name")
                if booking.get("attendees")
                else None,
                attendee_email=booking.get("attendees", [{}])[0].get("email")
                if booking.get("attendees")
                else None,
                location=booking.get("location"),
            )
            for booking in bookings_data
        ]

        logger.info("Cal.com list bookings complete count=%d", len(bookings))

        return CalcomListBookingsResponse(
            success=True,
            data=CalcomListBookingsData(
                bookings=bookings,
                status_filter=status,
            ),
        )
    except Exception as e:
        logger.exception("Cal.com list bookings failed")
        return CalcomListBookingsResponse(
            success=False, error=f"Cal.com list bookings failed: {str(e)}"
        )


@tool()
async def calcom_create_booking(
    event_type_id: int,
    start: str,
    name: str,
    email: str,
    timezone: str = "America/New_York",
    notes: str | None = None,
    location: str | None = None,
) -> CalcomCreateBookingResponse:
    """Create a new booking on Cal.com.

    Schedules a booking for a specific event type at the given start time.
    The event type determines the duration and other settings.

    Args:
        event_type_id: The Cal.com event type ID to book.
        start: Start time in ISO 8601 format (e.g., '2025-03-15T10:00:00Z').
        name: Attendee's full name.
        email: Attendee's email address.
        timezone: Attendee's timezone in IANA format (default: 'America/New_York').
        notes: Optional notes or message from the attendee.
        location: Optional meeting location or video link.

    Returns:
        Booking confirmation with UID, start time, and attendee details.
    """
    try:
        api_key_val = await resolve_credential("CALCOM_API_KEY")
        if not api_key_val:
            return CalcomCreateBookingResponse(
                success=False, error="Cal.com API not configured. Set CALCOM_API_KEY."
            )

        api_key, base_url = _get_calcom_config(api_key_val)

        logger.info(
            "Cal.com create booking start event_type_id=%d start=%s",
            event_type_id,
            start,
        )

        url = f"{base_url}/bookings"
        payload: dict = {
            "start": start,
            "eventTypeId": event_type_id,
            "attendee": {
                "name": name,
                "email": email,
                "timeZone": timezone,
            },
        }
        if notes:
            payload["attendee"]["notes"] = notes
        if location:
            payload["location"] = location

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url, headers=_calcom_headers(api_key), json=payload
            )
            response.raise_for_status()

        booking_data = response.json().get("data", {})

        logger.info(
            "Cal.com create booking complete uid=%s",
            booking_data.get("uid"),
        )

        return CalcomCreateBookingResponse(
            success=True,
            data=CalcomCreateBookingData(
                uid=booking_data["uid"],
                start_time=booking_data.get("start", start),
                event_type_id=event_type_id,
                attendee_name=name,
                attendee_email=email,
            ),
        )
    except Exception as e:
        logger.exception("Cal.com create booking failed")
        return CalcomCreateBookingResponse(
            success=False, error=f"Cal.com create booking failed: {str(e)}"
        )


@tool()
async def calcom_cancel_booking(
    booking_uid: str,
    reason: str | None = None,
) -> CalcomCancelBookingResponse:
    """Cancel an existing Cal.com booking.

    Cancels a booking identified by its UID.  An optional cancellation reason
    can be provided which will be communicated to the attendee.

    Args:
        booking_uid: The unique identifier (UID) of the booking to cancel.
        reason: Optional reason for cancellation.

    Returns:
        Cancellation confirmation.
    """
    try:
        api_key_val = await resolve_credential("CALCOM_API_KEY")
        if not api_key_val:
            return CalcomCancelBookingResponse(
                success=False, error="Cal.com API not configured. Set CALCOM_API_KEY."
            )

        api_key, base_url = _get_calcom_config(api_key_val)

        logger.info("Cal.com cancel booking uid=%s", booking_uid)

        url = f"{base_url}/bookings/{booking_uid}/cancel"
        payload: dict = {}
        if reason:
            payload["cancellationReason"] = reason

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url, headers=_calcom_headers(api_key), json=payload
            )
            response.raise_for_status()

        logger.info("Cal.com cancel booking complete uid=%s", booking_uid)

        return CalcomCancelBookingResponse(
            success=True,
            data=CalcomCancelBookingData(
                uid=booking_uid,
                message=f"Booking {booking_uid} cancelled successfully",
            ),
        )
    except Exception as e:
        logger.exception("Cal.com cancel booking failed")
        return CalcomCancelBookingResponse(
            success=False, error=f"Cal.com cancel booking failed: {str(e)}"
        )


@tool()
async def calcom_reschedule_booking(
    booking_uid: str,
    new_start: str,
    reason: str | None = None,
) -> CalcomRescheduleBookingResponse:
    """Reschedule an existing Cal.com booking to a new time.

    Moves a booking to a new start time.  The original booking is replaced
    with a new one at the requested time.

    Args:
        booking_uid: The unique identifier (UID) of the booking to reschedule.
        new_start: New start time in ISO 8601 format (e.g., '2025-03-20T14:00:00Z').
        reason: Optional reason for rescheduling.

    Returns:
        Reschedule confirmation with new booking details.
    """
    try:
        api_key_val = await resolve_credential("CALCOM_API_KEY")
        if not api_key_val:
            return CalcomRescheduleBookingResponse(
                success=False, error="Cal.com API not configured. Set CALCOM_API_KEY."
            )

        api_key, base_url = _get_calcom_config(api_key_val)

        logger.info(
            "Cal.com reschedule booking uid=%s new_start=%s",
            booking_uid,
            new_start,
        )

        url = f"{base_url}/bookings/{booking_uid}/reschedule"
        payload: dict = {"start": new_start}
        if reason:
            payload["reschedulingReason"] = reason

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url, headers=_calcom_headers(api_key), json=payload
            )
            response.raise_for_status()

        result = response.json().get("data", {})
        new_uid = result.get("uid", booking_uid)

        logger.info(
            "Cal.com reschedule booking complete old_uid=%s new_uid=%s",
            booking_uid,
            new_uid,
        )

        return CalcomRescheduleBookingResponse(
            success=True,
            data=CalcomRescheduleBookingData(
                uid=new_uid,
                start_time=result.get("start", new_start),
                message=f"Booking rescheduled to {new_start}",
            ),
        )
    except Exception as e:
        logger.exception("Cal.com reschedule booking failed")
        return CalcomRescheduleBookingResponse(
            success=False, error=f"Cal.com reschedule booking failed: {str(e)}"
        )


@tool()
async def calcom_get_availability(
    event_type_id: int,
    date_from: str,
    date_to: str,
) -> CalcomAvailabilityResponse:
    """Get available time slots for a Cal.com event type.

    Retrieves open slots within a date range for the specified event type.
    Useful for finding available times before creating a booking.

    Args:
        event_type_id: The Cal.com event type ID to check availability for.
        date_from: Start date in YYYY-MM-DD format.
        date_to: End date in YYYY-MM-DD format.

    Returns:
        List of available time slots within the date range.
    """
    try:
        api_key_val = await resolve_credential("CALCOM_API_KEY")
        if not api_key_val:
            return CalcomAvailabilityResponse(
                success=False, error="Cal.com API not configured. Set CALCOM_API_KEY."
            )

        api_key, base_url = _get_calcom_config(api_key_val)

        logger.info(
            "Cal.com get availability start event_type_id=%d from=%s to=%s",
            event_type_id,
            date_from,
            date_to,
        )

        url = f"{base_url}/slots/available"
        params = {
            "startTime": f"{date_from}T00:00:00Z",
            "endTime": f"{date_to}T23:59:59Z",
            "eventTypeId": str(event_type_id),
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                url, headers=_calcom_headers(api_key), params=params
            )
            response.raise_for_status()

        slots_data = response.json().get("data", {}).get("slots", {})

        slots = [
            CalcomAvailabilitySlot(time=slot["time"])
            for _date, time_slots in slots_data.items()
            for slot in time_slots
        ]

        logger.info("Cal.com get availability complete slots=%d", len(slots))

        return CalcomAvailabilityResponse(
            success=True,
            data=CalcomAvailabilityData(
                event_type_id=event_type_id,
                date_from=date_from,
                date_to=date_to,
                slots=slots,
            ),
        )
    except Exception as e:
        logger.exception("Cal.com get availability failed")
        return CalcomAvailabilityResponse(
            success=False,
            error=f"Cal.com get availability failed: {str(e)}",
        )


@tool()
async def calcom_list_event_types() -> CalcomListEventTypesResponse:
    """List all event types for the authenticated Cal.com user.

    Returns event types with their ID, title, slug, description, and duration.
    Event type IDs are needed for creating bookings and checking availability.

    Returns:
        List of event types with metadata.
    """
    try:
        api_key_val = await resolve_credential("CALCOM_API_KEY")
        if not api_key_val:
            return CalcomListEventTypesResponse(
                success=False, error="Cal.com API not configured. Set CALCOM_API_KEY."
            )

        api_key, base_url = _get_calcom_config(api_key_val)

        logger.info("Cal.com list event types start")

        url = f"{base_url}/event-types"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=_calcom_headers(api_key))
            response.raise_for_status()

        event_types_data = response.json().get("data", [])

        event_types = [
            CalcomEventType(
                id=et["id"],
                title=et.get("title", ""),
                slug=et.get("slug"),
                description=et.get("description"),
                length=et.get("length"),
                hidden=et.get("hidden"),
            )
            for et in event_types_data
        ]

        logger.info("Cal.com list event types complete count=%d", len(event_types))

        return CalcomListEventTypesResponse(
            success=True,
            data=CalcomListEventTypesData(
                event_types=event_types,
                count=len(event_types),
            ),
        )
    except Exception as e:
        logger.exception("Cal.com list event types failed")
        return CalcomListEventTypesResponse(
            success=False, error=f"Cal.com list event types failed: {str(e)}"
        )
