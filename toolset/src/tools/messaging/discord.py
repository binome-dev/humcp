"""Discord messaging tools for sending messages, managing reactions, threads, and channels.

Uses the Discord Bot API v10 (https://discord.com/developers/docs).
Requires the DISCORD_BOT_TOKEN environment variable to be set.
"""

from __future__ import annotations

import logging
import os
from urllib.parse import quote as url_quote

from src.humcp.decorator import tool
from src.tools.messaging.schemas import (
    AddReactionResponse,
    ChannelInfo,
    DiscordCreateThreadResponse,
    DiscordMessageInfo,
    DiscordThreadCreatedData,
    GetMessagesData,
    GetMessagesResponse,
    ListChannelsData,
    ListChannelsResponse,
    MessageSentData,
    ReactionAddedData,
    SendMessageResponse,
)

try:
    import httpx
except ImportError as err:
    raise ImportError(
        "httpx is required for Discord tools. Install with: pip install httpx"
    ) from err

logger = logging.getLogger("humcp.tools.discord")

DISCORD_API_BASE = "https://discord.com/api/v10"


def _get_headers() -> dict[str, str] | None:
    """Build Discord API headers from the environment token."""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        return None
    return {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }


@tool()
async def discord_send_message(
    channel_id: str,
    content: str,
    embed_title: str | None = None,
    embed_description: str | None = None,
) -> SendMessageResponse:
    """Send a message to a Discord channel, optionally with a rich embed.

    Uses the POST /channels/{channel_id}/messages endpoint.
    Requires the SEND_MESSAGES permission in the target channel.

    Args:
        channel_id: The ID of the Discord channel to send the message to.
        content: The text content of the message (up to 2000 characters).
        embed_title: Optional title for a rich embed attached to the message.
        embed_description: Optional description for the rich embed (up to 4096 characters).

    Returns:
        Response indicating success with message details, or an error.
    """
    try:
        headers = _get_headers()
        if headers is None:
            return SendMessageResponse(
                success=False,
                error="Discord not configured. Set DISCORD_BOT_TOKEN environment variable.",
            )

        payload: dict = {"content": content}
        if embed_title or embed_description:
            embed: dict = {}
            if embed_title:
                embed["title"] = embed_title
            if embed_description:
                embed["description"] = embed_description
            payload["embeds"] = [embed]

        logger.info("Sending Discord message to channel_id=%s", channel_id)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
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
                channel=data.get("channel_id"),
                timestamp=data.get("timestamp"),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Discord send_message HTTP error")
        return SendMessageResponse(
            success=False,
            error=f"Discord API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Discord send_message failed")
        return SendMessageResponse(
            success=False, error=f"Failed to send Discord message: {str(e)}"
        )


@tool()
async def discord_add_reaction(
    channel_id: str, message_id: str, emoji: str
) -> AddReactionResponse:
    """Add a reaction emoji to a Discord message.

    Uses the PUT /channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me endpoint.
    Requires READ_MESSAGE_HISTORY permission. Also requires ADD_REACTIONS if no one
    else has reacted with the same emoji yet.

    Args:
        channel_id: The ID of the channel containing the message.
        message_id: The ID of the message to react to.
        emoji: The emoji to react with. Use Unicode emoji (e.g., "thumbsup") or
               custom emoji in the format "name:id" (e.g., "myemoji:123456789").

    Returns:
        Response indicating success, or an error.
    """
    try:
        headers = _get_headers()
        if headers is None:
            return AddReactionResponse(
                success=False,
                error="Discord not configured. Set DISCORD_BOT_TOKEN environment variable.",
            )

        encoded_emoji = url_quote(emoji)
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me"

        logger.info(
            "Adding reaction emoji=%s to message=%s in channel=%s",
            emoji,
            message_id,
            channel_id,
        )
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

        return AddReactionResponse(
            success=True,
            data=ReactionAddedData(
                message_id=message_id,
                emoji=emoji,
                channel_id=channel_id,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Discord add_reaction HTTP error")
        return AddReactionResponse(
            success=False,
            error=f"Discord API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Discord add_reaction failed")
        return AddReactionResponse(
            success=False, error=f"Failed to add Discord reaction: {str(e)}"
        )


@tool()
async def discord_get_messages(channel_id: str, limit: int = 50) -> GetMessagesResponse:
    """Fetch recent messages from a Discord channel.

    Uses the GET /channels/{channel_id}/messages endpoint.
    Requires the READ_MESSAGE_HISTORY permission.

    Args:
        channel_id: The ID of the Discord channel to fetch messages from.
        limit: Maximum number of messages to retrieve (1-100, default 50).

    Returns:
        Response containing a list of messages from the channel.
    """
    try:
        headers = _get_headers()
        if headers is None:
            return GetMessagesResponse(
                success=False,
                error="Discord not configured. Set DISCORD_BOT_TOKEN environment variable.",
            )

        if limit < 1:
            return GetMessagesResponse(success=False, error="limit must be at least 1")

        capped_limit = min(limit, 100)
        logger.info(
            "Fetching Discord messages channel_id=%s limit=%d", channel_id, capped_limit
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
                headers=headers,
                params={"limit": capped_limit},
                timeout=30,
            )
            response.raise_for_status()
            raw_messages = response.json()

        messages = [
            DiscordMessageInfo(
                id=msg["id"],
                content=msg.get("content", ""),
                author=msg.get("author", {}).get("username"),
                timestamp=msg.get("timestamp"),
                channel_id=msg.get("channel_id"),
            )
            for msg in raw_messages
        ]

        return GetMessagesResponse(
            success=True,
            data=GetMessagesData(
                messages=messages, count=len(messages), channel_id=channel_id
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Discord get_messages HTTP error")
        return GetMessagesResponse(
            success=False,
            error=f"Discord API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Discord get_messages failed")
        return GetMessagesResponse(
            success=False, error=f"Failed to get Discord messages: {str(e)}"
        )


@tool()
async def discord_list_channels(guild_id: str) -> ListChannelsResponse:
    """List all channels in a Discord server (guild).

    Uses the GET /guilds/{guild_id}/channels endpoint.
    Returns text, voice, category, news, stage, and forum channel types.

    Args:
        guild_id: The ID of the Discord server (guild) to list channels from.

    Returns:
        Response containing a list of channels with their IDs, names, and types.
    """
    try:
        headers = _get_headers()
        if headers is None:
            return ListChannelsResponse(
                success=False,
                error="Discord not configured. Set DISCORD_BOT_TOKEN environment variable.",
            )

        logger.info("Listing Discord channels for guild_id=%s", guild_id)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DISCORD_API_BASE}/guilds/{guild_id}/channels",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            raw_channels = response.json()

        # Discord channel types: 0=text, 2=voice, 4=category, 5=news, 13=stage, 15=forum
        type_map = {
            0: "text",
            2: "voice",
            4: "category",
            5: "news",
            13: "stage",
            15: "forum",
        }

        channels = [
            ChannelInfo(
                id=ch["id"],
                name=ch.get("name", ""),
                type=type_map.get(ch.get("type", 0), "other"),
            )
            for ch in raw_channels
        ]

        return ListChannelsResponse(
            success=True,
            data=ListChannelsData(channels=channels, count=len(channels)),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Discord list_channels HTTP error")
        return ListChannelsResponse(
            success=False,
            error=f"Discord API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Discord list_channels failed")
        return ListChannelsResponse(
            success=False, error=f"Failed to list Discord channels: {str(e)}"
        )


@tool()
async def discord_create_thread(
    channel_id: str,
    name: str,
    message_id: str | None = None,
    auto_archive_duration: int = 1440,
) -> DiscordCreateThreadResponse:
    """Create a new thread in a Discord channel.

    When message_id is provided, creates a thread attached to that message
    (uses POST /channels/{channel_id}/messages/{message_id}/threads).
    Otherwise creates a standalone thread without an associated message
    (uses POST /channels/{channel_id}/threads).

    Args:
        channel_id: The ID of the channel to create the thread in.
        name: The name of the thread (1-100 characters).
        message_id: Optional message ID to start the thread from.
                    When omitted, creates a standalone thread.
        auto_archive_duration: Duration in minutes before the thread is
                               automatically archived. Must be one of:
                               60 (1 hour), 1440 (1 day, default), 4320 (3 days),
                               or 10080 (7 days, requires server boost level 2).

    Returns:
        Response indicating success with the new thread details, or an error.
    """
    try:
        headers = _get_headers()
        if headers is None:
            return DiscordCreateThreadResponse(
                success=False,
                error="Discord not configured. Set DISCORD_BOT_TOKEN environment variable.",
            )

        payload: dict = {
            "name": name,
            "auto_archive_duration": auto_archive_duration,
        }

        if message_id:
            url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}/threads"
        else:
            url = f"{DISCORD_API_BASE}/channels/{channel_id}/threads"
            # Standalone threads require a type; 11 = public thread
            payload["type"] = 11

        logger.info(
            "Creating Discord thread name=%s in channel=%s message=%s",
            name,
            channel_id,
            message_id,
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        thread_type_map = {
            10: "news",
            11: "public",
            12: "private",
        }

        return DiscordCreateThreadResponse(
            success=True,
            data=DiscordThreadCreatedData(
                thread_id=data["id"],
                name=data.get("name", name),
                channel_id=channel_id,
                type=thread_type_map.get(data.get("type"), "public"),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("Discord create_thread HTTP error")
        return DiscordCreateThreadResponse(
            success=False,
            error=f"Discord API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Discord create_thread failed")
        return DiscordCreateThreadResponse(
            success=False, error=f"Failed to create Discord thread: {str(e)}"
        )
