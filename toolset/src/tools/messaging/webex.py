"""Webex messaging tools for sending messages, managing rooms, and listing participants.

Uses the Webex REST API v1 (https://developer.webex.com/docs/api/v1/).
Note: Webex "rooms" are also known as "spaces" in the Webex UI.
Requires the WEBEX_ACCESS_TOKEN environment variable.
"""

from __future__ import annotations

import logging
import os

from src.humcp.decorator import tool
from src.tools.messaging.schemas import (
    CreateRoomResponse,
    GetRoomDetailsResponse,
    ListRoomsData,
    ListRoomsResponse,
    MessageSentData,
    SendMessageResponse,
    WebexRoomCreatedData,
    WebexRoomDetailsData,
    WebexRoomInfo,
)

try:
    import httpx
except ImportError as err:
    raise ImportError(
        "httpx is required for Webex tools. Install with: pip install httpx"
    ) from err

logger = logging.getLogger("humcp.tools.webex")

WEBEX_API_BASE = "https://webexapis.com/v1"


def _get_headers() -> dict[str, str] | None:
    """Build Webex API headers from the environment token."""
    token = os.getenv("WEBEX_ACCESS_TOKEN")
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


@tool()
async def webex_send_message(
    room_id: str,
    text: str | None = None,
    markdown: str | None = None,
) -> SendMessageResponse:
    """Send a message to a Webex room (space).

    Uses the POST /messages endpoint. You can send plain text, Markdown, or both.
    If both are provided, Markdown is used for rich rendering and plain text
    serves as the fallback.

    Args:
        room_id: The ID of the Webex room to send the message to.
        text: Plain text message content. Used as a fallback when markdown
              is also provided, or as the primary content when markdown is omitted.
        markdown: Markdown-formatted message content. Supports bold (**), italic (*),
                  links [text](url), ordered/unordered lists, headings, code blocks,
                  and mentions (<@personId>). Max 7439 bytes.

    Returns:
        Response indicating success with message details, or an error.
    """
    try:
        headers = _get_headers()
        if headers is None:
            return SendMessageResponse(
                success=False,
                error="Webex not configured. Set WEBEX_ACCESS_TOKEN environment variable.",
            )

        if not text and not markdown:
            return SendMessageResponse(
                success=False,
                error="Either text or markdown must be provided.",
            )

        payload: dict = {"roomId": room_id}
        if text:
            payload["text"] = text
        if markdown:
            payload["markdown"] = markdown

        logger.info("Sending Webex message to room_id=%s", room_id)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WEBEX_API_BASE}/messages",
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        return SendMessageResponse(
            success=True,
            data=MessageSentData(
                message_id=data.get("id"),
                channel=data.get("roomId"),
                timestamp=data.get("created"),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Webex send_message HTTP error")
        return SendMessageResponse(
            success=False,
            error=f"Webex API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Webex send_message failed")
        return SendMessageResponse(
            success=False, error=f"Failed to send Webex message: {str(e)}"
        )


@tool()
async def webex_create_room(
    title: str, team_id: str | None = None
) -> CreateRoomResponse:
    """Create a new Webex room (space).

    Uses the POST /rooms endpoint. The authenticated user is automatically
    added as a member. If team_id is provided, the room is created within
    that team (and cannot be moved later).

    Args:
        title: The title of the new room.
        team_id: Optional team ID to associate the room with.

    Returns:
        Response indicating success with the new room details.
    """
    try:
        headers = _get_headers()
        if headers is None:
            return CreateRoomResponse(
                success=False,
                error="Webex not configured. Set WEBEX_ACCESS_TOKEN environment variable.",
            )

        payload: dict = {"title": title}
        if team_id:
            payload["teamId"] = team_id

        logger.info("Creating Webex room title=%s", title)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WEBEX_API_BASE}/rooms",
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        return CreateRoomResponse(
            success=True,
            data=WebexRoomCreatedData(
                id=data["id"],
                title=data.get("title", title),
                type=data.get("type"),
                created=data.get("created"),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Webex create_room HTTP error")
        return CreateRoomResponse(
            success=False,
            error=f"Webex API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Webex create_room failed")
        return CreateRoomResponse(
            success=False, error=f"Failed to create Webex room: {str(e)}"
        )


@tool()
async def webex_get_room_details(room_id: str) -> GetRoomDetailsResponse:
    """Get detailed information about a Webex room (space).

    Uses the GET /rooms/{roomId} endpoint. Returns the room's title, type,
    lock status, team association, and creation details.

    Args:
        room_id: The ID of the Webex room to get details for.

    Returns:
        Response containing the room's detailed information.
    """
    try:
        headers = _get_headers()
        if headers is None:
            return GetRoomDetailsResponse(
                success=False,
                error="Webex not configured. Set WEBEX_ACCESS_TOKEN environment variable.",
            )

        logger.info("Fetching Webex room details room_id=%s", room_id)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WEBEX_API_BASE}/rooms/{room_id}",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        return GetRoomDetailsResponse(
            success=True,
            data=WebexRoomDetailsData(
                id=data["id"],
                title=data.get("title", ""),
                type=data.get("type"),
                is_locked=data.get("isLocked"),
                team_id=data.get("teamId"),
                created=data.get("created"),
                creator_id=data.get("creatorId"),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Webex get_room_details HTTP error")
        return GetRoomDetailsResponse(
            success=False,
            error=f"Webex API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Webex get_room_details failed")
        return GetRoomDetailsResponse(
            success=False, error=f"Failed to get Webex room details: {str(e)}"
        )


@tool()
async def webex_list_rooms() -> ListRoomsResponse:
    """List all rooms (spaces) the Webex bot or user is a member of.

    Uses the GET /rooms endpoint. Returns up to 100 rooms sorted by
    last activity.

    Returns:
        Response containing a list of rooms with their IDs, titles, and types.
    """
    try:
        headers = _get_headers()
        if headers is None:
            return ListRoomsResponse(
                success=False,
                error="Webex not configured. Set WEBEX_ACCESS_TOKEN environment variable.",
            )

        logger.info("Listing Webex rooms")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WEBEX_API_BASE}/rooms",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        raw_rooms = data.get("items", [])
        rooms = [
            WebexRoomInfo(
                id=room["id"],
                title=room.get("title", ""),
                type=room.get("type"),
                is_locked=room.get("isLocked"),
                created=room.get("created"),
            )
            for room in raw_rooms
        ]

        return ListRoomsResponse(
            success=True,
            data=ListRoomsData(rooms=rooms, count=len(rooms)),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Webex list_rooms HTTP error")
        return ListRoomsResponse(
            success=False,
            error=f"Webex API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Webex list_rooms failed")
        return ListRoomsResponse(
            success=False, error=f"Failed to list Webex rooms: {str(e)}"
        )
