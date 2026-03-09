"""Telegram Bot API tools for sending messages, photos, and managing updates.

Uses the Telegram Bot API (https://core.telegram.org/bots/api).
Requires the TELEGRAM_BOT_TOKEN environment variable.
"""

from __future__ import annotations

import logging
import os

from src.humcp.decorator import tool
from src.tools.messaging.schemas import (
    EditTelegramMessageResponse,
    MessageSentData,
    SendMessageResponse,
    SendTelegramPhotoResponse,
    TelegramEditedMessageData,
    TelegramPhotoSentData,
    TelegramPinMessageResponse,
    TelegramPinnedMessageData,
    TelegramUpdate,
    TelegramUpdatesData,
    TelegramUpdatesResponse,
)

try:
    import httpx
except ImportError as err:
    raise ImportError(
        "httpx is required for Telegram tools. Install with: pip install httpx"
    ) from err

logger = logging.getLogger("humcp.tools.telegram")

TELEGRAM_API_BASE = "https://api.telegram.org"


def _get_bot_url() -> str | None:
    """Build the Telegram Bot API base URL from the environment token."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return None
    return f"{TELEGRAM_API_BASE}/bot{token}"


@tool()
async def telegram_send_message(
    chat_id: str,
    text: str,
    parse_mode: str | None = None,
    disable_notification: bool = False,
    reply_to_message_id: int | None = None,
) -> SendMessageResponse:
    """Send a text message to a Telegram chat.

    Uses the sendMessage Bot API method.

    Args:
        chat_id: The unique identifier for the target chat or username of the
                 target channel (in the format @channelusername).
        text: The text of the message to send (1-4096 characters).
        parse_mode: Optional formatting mode. One of "MarkdownV2", "HTML", or
                    "Markdown" (legacy). When set, special characters must be
                    escaped according to the chosen mode.
        disable_notification: If true, the message is sent silently and users
                              receive a notification with no sound.
        reply_to_message_id: Optional message ID to reply to, making this
                             message a reply in the conversation.

    Returns:
        Response indicating success with message details, or an error.
    """
    try:
        bot_url = _get_bot_url()
        if bot_url is None:
            return SendMessageResponse(
                success=False,
                error="Telegram not configured. Set TELEGRAM_BOT_TOKEN environment variable.",
            )

        payload: dict = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if disable_notification:
            payload["disable_notification"] = True
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id

        logger.info("Sending Telegram message to chat_id=%s", chat_id)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{bot_url}/sendMessage",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        if not data.get("ok"):
            return SendMessageResponse(
                success=False,
                error=f"Telegram API error: {data.get('description', 'Unknown error')}",
            )

        result = data.get("result", {})
        return SendMessageResponse(
            success=True,
            data=MessageSentData(
                message_id=str(result.get("message_id", "")),
                channel=str(result.get("chat", {}).get("id", "")),
                timestamp=str(result.get("date", "")),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Telegram send_message HTTP error")
        return SendMessageResponse(
            success=False,
            error=f"Telegram API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Telegram send_message failed")
        return SendMessageResponse(
            success=False, error=f"Failed to send Telegram message: {str(e)}"
        )


@tool()
async def telegram_send_photo(
    chat_id: str,
    photo_url: str,
    caption: str | None = None,
    parse_mode: str | None = None,
) -> SendTelegramPhotoResponse:
    """Send a photo to a Telegram chat via URL.

    Uses the sendPhoto Bot API method. The photo must be accessible via a
    public URL. For file uploads, use the Telegram file upload endpoint instead.

    Args:
        chat_id: The unique identifier for the target chat or username of the
                 target channel (in the format @channelusername).
        photo_url: URL of the photo to send. Telegram will download the image
                   from this URL. Must be a direct link to an image file
                   (JPEG, PNG, etc.) and less than 10 MB.
        caption: Optional caption for the photo (0-1024 characters).
        parse_mode: Optional formatting mode for the caption. One of
                    "MarkdownV2", "HTML", or "Markdown" (legacy).

    Returns:
        Response indicating success with the sent photo message details.
    """
    try:
        bot_url = _get_bot_url()
        if bot_url is None:
            return SendTelegramPhotoResponse(
                success=False,
                error="Telegram not configured. Set TELEGRAM_BOT_TOKEN environment variable.",
            )

        payload: dict = {"chat_id": chat_id, "photo": photo_url}
        if caption:
            payload["caption"] = caption
        if parse_mode:
            payload["parse_mode"] = parse_mode

        logger.info("Sending Telegram photo to chat_id=%s", chat_id)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{bot_url}/sendPhoto",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        if not data.get("ok"):
            return SendTelegramPhotoResponse(
                success=False,
                error=f"Telegram API error: {data.get('description', 'Unknown error')}",
            )

        result = data.get("result", {})
        return SendTelegramPhotoResponse(
            success=True,
            data=TelegramPhotoSentData(
                message_id=str(result.get("message_id", "")),
                chat_id=str(result.get("chat", {}).get("id", "")),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Telegram send_photo HTTP error")
        return SendTelegramPhotoResponse(
            success=False,
            error=f"Telegram API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Telegram send_photo failed")
        return SendTelegramPhotoResponse(
            success=False, error=f"Failed to send Telegram photo: {str(e)}"
        )


@tool()
async def telegram_edit_message(
    chat_id: str,
    message_id: int,
    text: str,
    parse_mode: str | None = None,
) -> EditTelegramMessageResponse:
    """Edit the text of a previously sent Telegram message.

    Uses the editMessageText Bot API method. Can only edit messages sent by the
    bot itself (not messages from other users).

    Args:
        chat_id: The unique identifier for the chat containing the message.
        message_id: The ID of the message to edit.
        text: The new text of the message (1-4096 characters).
        parse_mode: Optional formatting mode. One of "MarkdownV2", "HTML",
                    or "Markdown" (legacy).

    Returns:
        Response indicating success with the edited message details.
    """
    try:
        bot_url = _get_bot_url()
        if bot_url is None:
            return EditTelegramMessageResponse(
                success=False,
                error="Telegram not configured. Set TELEGRAM_BOT_TOKEN environment variable.",
            )

        payload: dict = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        logger.info(
            "Editing Telegram message chat_id=%s message_id=%d", chat_id, message_id
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{bot_url}/editMessageText",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        if not data.get("ok"):
            return EditTelegramMessageResponse(
                success=False,
                error=f"Telegram API error: {data.get('description', 'Unknown error')}",
            )

        result = data.get("result", {})
        return EditTelegramMessageResponse(
            success=True,
            data=TelegramEditedMessageData(
                message_id=str(result.get("message_id", "")),
                chat_id=str(result.get("chat", {}).get("id", "")),
                text=result.get("text"),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Telegram edit_message HTTP error")
        return EditTelegramMessageResponse(
            success=False,
            error=f"Telegram API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Telegram edit_message failed")
        return EditTelegramMessageResponse(
            success=False, error=f"Failed to edit Telegram message: {str(e)}"
        )


@tool()
async def telegram_get_updates(
    limit: int = 10, offset: int | None = None
) -> TelegramUpdatesResponse:
    """Get recent updates (incoming messages) from the Telegram bot.

    Uses the getUpdates Bot API method. Returns updates in chronological order.
    Use the offset parameter to acknowledge processed updates and avoid
    receiving them again.

    Args:
        limit: Maximum number of updates to retrieve (default 10, max 100).
        offset: Identifier of the first update to return. Set to
                last_update_id + 1 to acknowledge all previous updates.

    Returns:
        Response containing a list of recent updates.
    """
    try:
        bot_url = _get_bot_url()
        if bot_url is None:
            return TelegramUpdatesResponse(
                success=False,
                error="Telegram not configured. Set TELEGRAM_BOT_TOKEN environment variable.",
            )

        if limit < 1:
            return TelegramUpdatesResponse(
                success=False, error="limit must be at least 1"
            )

        capped_limit = min(limit, 100)
        params: dict = {"limit": capped_limit}
        if offset is not None:
            params["offset"] = offset

        logger.info(
            "Fetching Telegram updates limit=%d offset=%s", capped_limit, offset
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{bot_url}/getUpdates",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        if not data.get("ok"):
            return TelegramUpdatesResponse(
                success=False,
                error=f"Telegram API error: {data.get('description', 'Unknown error')}",
            )

        raw_updates = data.get("result", [])
        updates = [
            TelegramUpdate(
                update_id=u["update_id"],
                message_text=u.get("message", {}).get("text"),
                chat_id=u.get("message", {}).get("chat", {}).get("id"),
                from_user=u.get("message", {}).get("from", {}).get("username"),
                date=u.get("message", {}).get("date"),
            )
            for u in raw_updates
        ]

        return TelegramUpdatesResponse(
            success=True,
            data=TelegramUpdatesData(updates=updates, count=len(updates)),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Telegram get_updates HTTP error")
        return TelegramUpdatesResponse(
            success=False,
            error=f"Telegram API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Telegram get_updates failed")
        return TelegramUpdatesResponse(
            success=False, error=f"Failed to get Telegram updates: {str(e)}"
        )


@tool()
async def telegram_pin_message(
    chat_id: str,
    message_id: int,
    disable_notification: bool = False,
) -> TelegramPinMessageResponse:
    """Pin a message in a Telegram chat.

    Uses the pinChatMessage Bot API method. The bot must be an administrator
    in the group or channel with the can_pin_messages permission.

    Args:
        chat_id: The unique identifier for the chat or username of the
                 target channel (in the format @channelusername).
        message_id: The ID of the message to pin.
        disable_notification: If true, the notification is sent silently
                              and users receive a notification with no sound.

    Returns:
        Response indicating success, or an error.
    """
    try:
        bot_url = _get_bot_url()
        if bot_url is None:
            return TelegramPinMessageResponse(
                success=False,
                error="Telegram not configured. Set TELEGRAM_BOT_TOKEN environment variable.",
            )

        payload: dict = {
            "chat_id": chat_id,
            "message_id": message_id,
        }
        if disable_notification:
            payload["disable_notification"] = True

        logger.info(
            "Pinning Telegram message chat_id=%s message_id=%d", chat_id, message_id
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{bot_url}/pinChatMessage",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        if not data.get("ok"):
            return TelegramPinMessageResponse(
                success=False,
                error=f"Telegram API error: {data.get('description', 'Unknown error')}",
            )

        return TelegramPinMessageResponse(
            success=True,
            data=TelegramPinnedMessageData(
                chat_id=chat_id,
                message_id=message_id,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Telegram pin_message HTTP error")
        return TelegramPinMessageResponse(
            success=False,
            error=f"Telegram API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Telegram pin_message failed")
        return TelegramPinMessageResponse(
            success=False, error=f"Failed to pin Telegram message: {str(e)}"
        )
