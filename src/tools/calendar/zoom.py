"""Zoom meeting management tools.

Wraps the Zoom REST API v2 for creating, listing, updating, deleting meetings,
and retrieving meeting participants.  Uses Server-to-Server OAuth for
authentication.

Environment variables:
    ZOOM_ACCOUNT_ID: Zoom Server-to-Server OAuth account ID.
    ZOOM_CLIENT_ID: Zoom Server-to-Server OAuth client ID.
    ZOOM_CLIENT_SECRET: Zoom Server-to-Server OAuth client secret.
"""

from __future__ import annotations

import logging
from base64 import b64encode

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.calendar.schemas import (
    ZoomCreateMeetingData,
    ZoomCreateMeetingResponse,
    ZoomDeleteMeetingData,
    ZoomDeleteMeetingResponse,
    ZoomGetMeetingData,
    ZoomGetMeetingResponse,
    ZoomListMeetingsData,
    ZoomListMeetingsResponse,
    ZoomListParticipantsData,
    ZoomListParticipantsResponse,
    ZoomMeeting,
    ZoomMeetingParticipant,
    ZoomUpdateMeetingData,
    ZoomUpdateMeetingResponse,
)

logger = logging.getLogger("humcp.tools.zoom")

ZOOM_TOKEN_URL = "https://zoom.us/oauth/token"
ZOOM_API_BASE = "https://api.zoom.us/v2"

_NOT_CONFIGURED_MSG = "Zoom API not configured. Set ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, and ZOOM_CLIENT_SECRET."


async def _get_zoom_token() -> str | None:
    """Obtain a Zoom access token via Server-to-Server OAuth.

    Returns None if the required credentials are not available.
    """
    account_id = await resolve_credential("ZOOM_ACCOUNT_ID")
    client_id = await resolve_credential("ZOOM_CLIENT_ID")
    client_secret = await resolve_credential("ZOOM_CLIENT_SECRET")

    if not account_id or not client_id or not client_secret:
        return None

    auth_string = b64encode(f"{client_id}:{client_secret}".encode()).decode()

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            ZOOM_TOKEN_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth_string}",
            },
            data={
                "grant_type": "account_credentials",
                "account_id": account_id,
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def _zoom_request(
    endpoint: str,
    token: str,
    method: str = "GET",
    json_data: dict | None = None,
    params: dict | None = None,
) -> dict:
    """Make an authenticated request to the Zoom API.

    Returns the JSON response body, or ``{"success": True}`` for 204 responses.
    """
    url = f"{ZOOM_API_BASE}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=json_data,
            params=params,
        )
        if response.status_code == 204:
            return {"success": True}
        response.raise_for_status()
        return response.json()


@tool()
async def zoom_create_meeting(
    topic: str,
    start_time: str,
    duration: int,
    timezone: str = "UTC",
    agenda: str | None = None,
    password: str | None = None,
) -> ZoomCreateMeetingResponse:
    """Schedule a new Zoom meeting.

    Creates a scheduled meeting (type 2) with the specified topic, time,
    and duration.  Returns the meeting details including the join URL.

    Args:
        topic: The topic or title of the meeting.
        start_time: Start time in ISO 8601 format (e.g., '2025-03-15T10:00:00Z').
        duration: Duration of the meeting in minutes (1-1440).
        timezone: Timezone for the meeting in IANA format (default: 'UTC').
            Examples: 'America/New_York', 'Europe/London', 'Asia/Tokyo'.
        agenda: Optional meeting description/agenda text.
        password: Optional meeting password (max 10 characters).

    Returns:
        Meeting details including ID, join URL, and password.
    """
    try:
        token = await _get_zoom_token()
        if not token:
            return ZoomCreateMeetingResponse(success=False, error=_NOT_CONFIGURED_MSG)

        logger.info(
            "Zoom create meeting start topic=%s start_time=%s duration=%d",
            topic,
            start_time,
            duration,
        )

        meeting_data: dict = {
            "topic": topic,
            "type": 2,
            "start_time": start_time,
            "duration": duration,
            "timezone": timezone,
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": False,
                "audio": "voip",
                "auto_recording": "none",
            },
        }
        if agenda:
            meeting_data["agenda"] = agenda
        if password:
            meeting_data["password"] = password

        result = await _zoom_request(
            "users/me/meetings", token, method="POST", json_data=meeting_data
        )

        logger.info(
            "Zoom create meeting complete meeting_id=%s",
            result.get("id"),
        )

        return ZoomCreateMeetingResponse(
            success=True,
            data=ZoomCreateMeetingData(
                meeting_id=str(result["id"]),
                topic=result["topic"],
                start_time=result["start_time"],
                duration=result["duration"],
                timezone=result.get("timezone", timezone),
                join_url=result["join_url"],
                password=result.get("password"),
            ),
        )
    except Exception as e:
        logger.exception("Zoom create meeting failed")
        return ZoomCreateMeetingResponse(
            success=False, error=f"Zoom create meeting failed: {str(e)}"
        )


@tool()
async def zoom_list_meetings(
    meeting_type: str = "scheduled",
    page_size: int = 30,
) -> ZoomListMeetingsResponse:
    """List Zoom meetings for the authenticated user.

    Returns meetings matching the specified type filter with pagination.

    Args:
        meeting_type: Type of meetings to return. Options:
            'scheduled' (default), 'live', 'upcoming', 'upcoming_meetings',
            'previous_meetings'.
        page_size: Number of records per page (1-300, default: 30).

    Returns:
        List of meetings with details.
    """
    try:
        token = await _get_zoom_token()
        if not token:
            return ZoomListMeetingsResponse(success=False, error=_NOT_CONFIGURED_MSG)

        logger.info("Zoom list meetings start type=%s", meeting_type)

        result = await _zoom_request(
            "users/me/meetings",
            token,
            params={"type": meeting_type, "page_size": min(page_size, 300)},
        )

        meetings_data = result.get("meetings", [])
        meetings = [
            ZoomMeeting(
                meeting_id=str(meeting["id"]),
                topic=meeting.get("topic", ""),
                start_time=meeting.get("start_time"),
                duration=meeting.get("duration"),
                timezone=meeting.get("timezone"),
                join_url=meeting.get("join_url"),
                status=meeting.get("status"),
                type=meeting.get("type"),
            )
            for meeting in meetings_data
        ]

        total_records = result.get("total_records", len(meetings))

        logger.info("Zoom list meetings complete count=%d", len(meetings))

        return ZoomListMeetingsResponse(
            success=True,
            data=ZoomListMeetingsData(
                meetings=meetings,
                total_records=total_records,
            ),
        )
    except Exception as e:
        logger.exception("Zoom list meetings failed")
        return ZoomListMeetingsResponse(
            success=False, error=f"Zoom list meetings failed: {str(e)}"
        )


@tool()
async def zoom_get_meeting(
    meeting_id: str,
) -> ZoomGetMeetingResponse:
    """Get details of a specific Zoom meeting.

    Retrieves full meeting details including topic, time, duration, timezone,
    join URL, and current status.

    Args:
        meeting_id: The Zoom meeting ID to retrieve.

    Returns:
        Meeting details.
    """
    try:
        token = await _get_zoom_token()
        if not token:
            return ZoomGetMeetingResponse(success=False, error=_NOT_CONFIGURED_MSG)

        logger.info("Zoom get meeting start meeting_id=%s", meeting_id)

        result = await _zoom_request(f"meetings/{meeting_id}", token)

        meeting = ZoomMeeting(
            meeting_id=str(result.get("id", meeting_id)),
            topic=result.get("topic", ""),
            start_time=result.get("start_time"),
            duration=result.get("duration"),
            timezone=result.get("timezone"),
            join_url=result.get("join_url"),
            status=result.get("status"),
            type=result.get("type"),
        )

        logger.info("Zoom get meeting complete topic=%s", meeting.topic)

        return ZoomGetMeetingResponse(
            success=True,
            data=ZoomGetMeetingData(meeting=meeting),
        )
    except Exception as e:
        logger.exception("Zoom get meeting failed")
        return ZoomGetMeetingResponse(
            success=False, error=f"Zoom get meeting failed: {str(e)}"
        )


@tool()
async def zoom_delete_meeting(
    meeting_id: str,
) -> ZoomDeleteMeetingResponse:
    """Delete a Zoom meeting.

    Permanently deletes the specified meeting.  This action cannot be undone.

    Args:
        meeting_id: The Zoom meeting ID to delete.

    Returns:
        Deletion confirmation.
    """
    try:
        token = await _get_zoom_token()
        if not token:
            return ZoomDeleteMeetingResponse(success=False, error=_NOT_CONFIGURED_MSG)

        logger.info("Zoom delete meeting start meeting_id=%s", meeting_id)

        await _zoom_request(f"meetings/{meeting_id}", token, method="DELETE")

        logger.info("Zoom delete meeting complete meeting_id=%s", meeting_id)

        return ZoomDeleteMeetingResponse(
            success=True,
            data=ZoomDeleteMeetingData(
                meeting_id=meeting_id,
                message=f"Meeting {meeting_id} deleted successfully",
            ),
        )
    except Exception as e:
        logger.exception("Zoom delete meeting failed")
        return ZoomDeleteMeetingResponse(
            success=False, error=f"Zoom delete meeting failed: {str(e)}"
        )


@tool()
async def zoom_update_meeting(
    meeting_id: str,
    topic: str | None = None,
    start_time: str | None = None,
    duration: int | None = None,
    timezone: str | None = None,
    agenda: str | None = None,
) -> ZoomUpdateMeetingResponse:
    """Update an existing Zoom meeting.

    Modifies meeting properties.  Only the provided fields are updated;
    omitted fields remain unchanged.

    Args:
        meeting_id: The Zoom meeting ID to update.
        topic: New meeting topic/title.
        start_time: New start time in ISO 8601 format.
        duration: New duration in minutes.
        timezone: New timezone in IANA format.
        agenda: New meeting agenda/description.

    Returns:
        Update confirmation.
    """
    try:
        token = await _get_zoom_token()
        if not token:
            return ZoomUpdateMeetingResponse(success=False, error=_NOT_CONFIGURED_MSG)

        logger.info("Zoom update meeting start meeting_id=%s", meeting_id)

        update_data: dict = {}
        if topic is not None:
            update_data["topic"] = topic
        if start_time is not None:
            update_data["start_time"] = start_time
        if duration is not None:
            update_data["duration"] = duration
        if timezone is not None:
            update_data["timezone"] = timezone
        if agenda is not None:
            update_data["agenda"] = agenda

        if not update_data:
            return ZoomUpdateMeetingResponse(
                success=False,
                error="No fields provided to update. Specify at least one of: topic, start_time, duration, timezone, agenda.",
            )

        await _zoom_request(
            f"meetings/{meeting_id}", token, method="PATCH", json_data=update_data
        )

        logger.info("Zoom update meeting complete meeting_id=%s", meeting_id)

        return ZoomUpdateMeetingResponse(
            success=True,
            data=ZoomUpdateMeetingData(
                meeting_id=meeting_id,
                message=f"Meeting {meeting_id} updated successfully",
            ),
        )
    except Exception as e:
        logger.exception("Zoom update meeting failed")
        return ZoomUpdateMeetingResponse(
            success=False, error=f"Zoom update meeting failed: {str(e)}"
        )


@tool()
async def zoom_list_meeting_participants(
    meeting_id: str,
) -> ZoomListParticipantsResponse:
    """List participants from a past Zoom meeting.

    Retrieves participant details from a completed meeting including join/leave
    times and duration.  Only works for past meetings.

    Args:
        meeting_id: The Zoom meeting ID (must be a past meeting).

    Returns:
        List of participants with join/leave times and duration.
    """
    try:
        token = await _get_zoom_token()
        if not token:
            return ZoomListParticipantsResponse(
                success=False, error=_NOT_CONFIGURED_MSG
            )

        logger.info("Zoom list participants start meeting_id=%s", meeting_id)

        result = await _zoom_request(f"past_meetings/{meeting_id}/participants", token)

        participants_data = result.get("participants", [])
        participants = [
            ZoomMeetingParticipant(
                name=p.get("name", "Unknown"),
                email=p.get("user_email"),
                join_time=p.get("join_time"),
                leave_time=p.get("leave_time"),
                duration=p.get("duration"),
            )
            for p in participants_data
        ]

        total_records = result.get("total_records", len(participants))

        logger.info(
            "Zoom list participants complete meeting_id=%s count=%d",
            meeting_id,
            len(participants),
        )

        return ZoomListParticipantsResponse(
            success=True,
            data=ZoomListParticipantsData(
                meeting_id=meeting_id,
                participants=participants,
                total_records=total_records,
            ),
        )
    except Exception as e:
        logger.exception("Zoom list participants failed")
        return ZoomListParticipantsResponse(
            success=False,
            error=f"Zoom list meeting participants failed: {str(e)}",
        )
