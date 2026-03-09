"""Google Calendar tools for listing, creating, and managing calendar events."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from src.humcp.decorator import tool
from src.tools.google.auth import SCOPES, get_google_service
from src.tools.google.schemas import (
    CalendarCreateEventData,
    CalendarCreateEventResponse,
    CalendarDeleteEventData,
    CalendarDeleteEventResponse,
    CalendarEvent,
    CalendarEventsData,
    CalendarEventsResponse,
    CalendarInfo,
    CalendarListData,
    CalendarListResponse,
    CalendarQuickAddData,
    CalendarQuickAddResponse,
)

logger = logging.getLogger("humcp.tools.google.calendar")

# Scopes required for Calendar operations
CALENDAR_READONLY_SCOPES = [SCOPES["calendar_readonly"]]
CALENDAR_FULL_SCOPES = [SCOPES["calendar"]]


@tool()
async def google_calendar_list() -> CalendarListResponse:
    """List all calendars accessible to the user.

    Returns a list of calendars with their IDs, names, descriptions,
    and access roles. Useful for finding the correct calendar ID
    before listing events or creating new ones.

    Returns:
        List of calendars with id, name, description, primary status, and access_role.
    """
    try:

        def _list():
            service = get_google_service("calendar", "v3", CALENDAR_READONLY_SCOPES)
            results = service.calendarList().list().execute()
            items = results.get("items", [])
            return [
                CalendarInfo(
                    id=cal["id"],
                    name=cal.get("summary", ""),
                    description=cal.get("description", ""),
                    primary=cal.get("primary", False),
                    access_role=cal.get("accessRole", ""),
                )
                for cal in items
            ]

        logger.info("calendar_list")
        calendars = await asyncio.to_thread(_list)
        return CalendarListResponse(
            success=True,
            data=CalendarListData(calendars=calendars, total=len(calendars)),
        )
    except Exception as e:
        logger.exception("calendar_list failed")
        return CalendarListResponse(success=False, error=str(e))


@tool()
async def google_calendar_events(
    calendar_id: str = "primary",
    days_ahead: int = 7,
    max_results: int = 50,
) -> CalendarEventsResponse:
    """List upcoming events from a calendar.

    Retrieves events starting from now up to the specified number of days ahead.
    Events are returned in chronological order by start time.

    Args:
        calendar_id: Calendar ID to list events from (default: "primary").
        days_ahead: Number of days to look ahead (default: 7).
        max_results: Maximum number of events to return (default: 50).

    Returns:
        List of events with id, title, description, start/end times, location, and status.
    """
    try:

        def _list_events():
            service = get_google_service("calendar", "v3", CALENDAR_READONLY_SCOPES)

            now = datetime.now(UTC)
            time_min = now.isoformat()
            time_max = (now + timedelta(days=days_ahead)).isoformat()

            results = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            items = results.get("items", [])
            return [
                CalendarEvent(
                    id=event["id"],
                    title=event.get("summary", "(no title)"),
                    description=event.get("description", ""),
                    start=event.get("start", {}).get(
                        "dateTime", event.get("start", {}).get("date", "")
                    ),
                    end=event.get("end", {}).get(
                        "dateTime", event.get("end", {}).get("date", "")
                    ),
                    location=event.get("location", ""),
                    status=event.get("status", ""),
                    html_link=event.get("htmlLink", ""),
                )
                for event in items
            ]

        logger.info(
            "calendar_events calendar_id=%s days_ahead=%s", calendar_id, days_ahead
        )
        events = await asyncio.to_thread(_list_events)
        return CalendarEventsResponse(
            success=True,
            data=CalendarEventsData(events=events, total=len(events)),
        )
    except Exception as e:
        logger.exception("calendar_events failed")
        return CalendarEventsResponse(success=False, error=str(e))


@tool()
async def google_calendar_create_event(
    title: str,
    start_time: str,
    end_time: str,
    calendar_id: str = "primary",
    description: str = "",
    location: str = "",
    attendees: str = "",
) -> CalendarCreateEventResponse:
    """Create a new calendar event.

    Creates an event with the specified details. Times should be in ISO 8601 format.

    Args:
        title: Event title/summary.
        start_time: Start time in ISO 8601 format (e.g., "2024-01-15T09:00:00Z").
        end_time: End time in ISO 8601 format.
        calendar_id: Calendar ID to create event in (default: "primary").
        description: Optional event description.
        location: Optional event location.
        attendees: Optional comma-separated list of attendee email addresses.

    Returns:
        Created event details including id, title, times, and html_link.
    """
    try:

        def _create():
            service = get_google_service("calendar", "v3", CALENDAR_FULL_SCOPES)

            event_body = {
                "summary": title,
                "description": description,
                "location": location,
                "start": {"dateTime": start_time, "timeZone": "UTC"},
                "end": {"dateTime": end_time, "timeZone": "UTC"},
            }

            if attendees:
                event_body["attendees"] = [
                    {"email": email.strip()} for email in attendees.split(",")
                ]

            event = (
                service.events()
                .insert(calendarId=calendar_id, body=event_body)
                .execute()
            )

            return CalendarCreateEventData(
                id=event["id"],
                title=event.get("summary"),
                start=event.get("start", {}).get("dateTime"),
                end=event.get("end", {}).get("dateTime"),
                html_link=event.get("htmlLink"),
            )

        logger.info("calendar_create_event title=%s", title)
        result = await asyncio.to_thread(_create)
        return CalendarCreateEventResponse(success=True, data=result)
    except Exception as e:
        logger.exception("calendar_create_event failed")
        return CalendarCreateEventResponse(success=False, error=str(e))


@tool()
async def google_calendar_delete_event(
    event_id: str,
    calendar_id: str = "primary",
) -> CalendarDeleteEventResponse:
    """Delete a calendar event.

    Permanently removes an event from the specified calendar.

    Args:
        event_id: ID of the event to delete.
        calendar_id: Calendar ID containing the event (default: "primary").

    Returns:
        Confirmation with the deleted event ID.
    """
    try:

        def _delete():
            service = get_google_service("calendar", "v3", CALENDAR_FULL_SCOPES)
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            return CalendarDeleteEventData(deleted_event_id=event_id)

        logger.info("calendar_delete_event event_id=%s", event_id)
        result = await asyncio.to_thread(_delete)
        return CalendarDeleteEventResponse(success=True, data=result)
    except Exception as e:
        logger.exception("calendar_delete_event failed")
        return CalendarDeleteEventResponse(success=False, error=str(e))


@tool()
async def google_calendar_quick_add(
    text: str,
    calendar_id: str = "primary",
) -> CalendarQuickAddResponse:
    """Create a calendar event from a natural language string.

    Uses the Google Calendar quickAdd endpoint which parses natural language
    into a structured event. For example: "Lunch with John at noon tomorrow",
    "Team standup 9am every weekday", "Flight to NYC on March 15 at 3pm".

    Args:
        text: Natural language description of the event. Google Calendar will
              parse the date, time, and title from this string.
        calendar_id: Calendar ID to add the event to (default: "primary").

    Returns:
        Created event details including parsed title, times, and link.
    """
    try:

        def _quick_add():
            service = get_google_service("calendar", "v3", CALENDAR_FULL_SCOPES)
            event = (
                service.events().quickAdd(calendarId=calendar_id, text=text).execute()
            )
            return CalendarQuickAddData(
                id=event["id"],
                title=event.get("summary"),
                start=event.get("start", {}).get(
                    "dateTime", event.get("start", {}).get("date")
                ),
                end=event.get("end", {}).get(
                    "dateTime", event.get("end", {}).get("date")
                ),
                html_link=event.get("htmlLink"),
            )

        logger.info("calendar_quick_add text=%s", text)
        result = await asyncio.to_thread(_quick_add)
        return CalendarQuickAddResponse(success=True, data=result)
    except Exception as e:
        logger.exception("calendar_quick_add failed")
        return CalendarQuickAddResponse(success=False, error=str(e))
