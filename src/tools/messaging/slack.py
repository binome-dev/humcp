"""Slack messaging tools for sending messages, managing reactions, threads, and channels.

Uses the Slack Web API via the slack_sdk Python package.
See https://docs.slack.dev/reference/methods/ for full API reference.
Requires the SLACK_TOKEN environment variable (Bot User OAuth Token).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from src.humcp.decorator import tool
from src.tools.messaging.schemas import (
    ChannelHistoryData,
    ChannelHistoryResponse,
    ChannelInfo,
    ListChannelsData,
    ListChannelsResponse,
    MessageInfo,
    MessageSentData,
    SearchMessagesData,
    SearchMessagesResponse,
    SendMessageResponse,
    SlackChannelTopicData,
    SlackReactionData,
    SlackReactionResponse,
    SlackSetChannelTopicResponse,
    SlackThreadReplyData,
    SlackThreadReplyResponse,
    SlackUserInfo,
    SlackUserInfoData,
    SlackUserInfoResponse,
)

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError as err:
    raise ImportError(
        "slack_sdk is required for Slack tools. Install with: pip install slack-sdk"
    ) from err

logger = logging.getLogger("humcp.tools.slack")


def _get_client() -> WebClient | None:
    """Create a Slack WebClient from the environment token."""
    token = os.getenv("SLACK_TOKEN")
    if not token:
        return None
    return WebClient(token=token)


@tool()
async def slack_send_message(
    channel: str, text: str, thread_ts: str | None = None
) -> SendMessageResponse:
    """Send a message to a Slack channel or thread.

    Uses the chat.postMessage API method. Supports Slack mrkdwn formatting.
    To reply in a thread, provide the thread_ts of the parent message.

    Args:
        channel: The channel ID or name to send the message to.
        text: The text of the message. Supports Slack mrkdwn formatting
              (e.g., *bold*, _italic_, ~strike~, `code`, ```code block```).
        thread_ts: Optional timestamp of the parent message to reply in a thread.
                   When set, the message is posted as a threaded reply.

    Returns:
        Response indicating success with message details, or an error.
    """
    try:
        client = _get_client()
        if client is None:
            return SendMessageResponse(
                success=False,
                error="Slack not configured. Set SLACK_TOKEN environment variable.",
            )

        logger.info(
            "Sending Slack message to channel=%s thread_ts=%s", channel, thread_ts
        )
        kwargs: dict = {"channel": channel, "text": text, "mrkdwn": True}
        if thread_ts:
            kwargs["thread_ts"] = thread_ts

        response = client.chat_postMessage(**kwargs)

        return SendMessageResponse(
            success=True,
            data=MessageSentData(
                message_id=response.get("ts"),
                channel=response.get("channel"),
                timestamp=response.get("ts"),
            ),
        )
    except SlackApiError as e:
        logger.exception("Slack send_message failed")
        return SendMessageResponse(
            success=False, error=f"Slack API error: {e.response['error']}"
        )
    except Exception as e:
        logger.exception("Slack send_message failed")
        return SendMessageResponse(
            success=False, error=f"Failed to send Slack message: {str(e)}"
        )


@tool()
async def slack_add_reaction(
    channel: str, timestamp: str, name: str
) -> SlackReactionResponse:
    """Add an emoji reaction to a Slack message.

    Uses the reactions.add API method. The bot must be in the channel.

    Args:
        channel: The channel ID containing the message.
        timestamp: The timestamp (ts) of the message to react to.
        name: The name of the emoji reaction without colons (e.g., "thumbsup",
              "heart", "white_check_mark").

    Returns:
        Response indicating success, or an error.
    """
    try:
        client = _get_client()
        if client is None:
            return SlackReactionResponse(
                success=False,
                error="Slack not configured. Set SLACK_TOKEN environment variable.",
            )

        logger.info(
            "Adding Slack reaction name=%s to channel=%s ts=%s",
            name,
            channel,
            timestamp,
        )
        client.reactions_add(channel=channel, timestamp=timestamp, name=name)

        return SlackReactionResponse(
            success=True,
            data=SlackReactionData(
                channel=channel,
                timestamp=timestamp,
                reaction=name,
            ),
        )
    except SlackApiError as e:
        logger.exception("Slack add_reaction failed")
        return SlackReactionResponse(
            success=False, error=f"Slack API error: {e.response['error']}"
        )
    except Exception as e:
        logger.exception("Slack add_reaction failed")
        return SlackReactionResponse(
            success=False, error=f"Failed to add Slack reaction: {str(e)}"
        )


@tool()
async def slack_get_thread_replies(
    channel: str, thread_ts: str, limit: int = 50
) -> SlackThreadReplyResponse:
    """Fetch replies in a Slack message thread.

    Uses the conversations.replies API method. Returns all messages in
    the thread, including the parent message.

    Args:
        channel: The channel ID containing the thread.
        thread_ts: The timestamp (ts) of the parent message that started the thread.
        limit: Maximum number of replies to retrieve (default 50, max 200).

    Returns:
        Response containing the thread messages.
    """
    try:
        client = _get_client()
        if client is None:
            return SlackThreadReplyResponse(
                success=False,
                error="Slack not configured. Set SLACK_TOKEN environment variable.",
            )

        if limit < 1:
            return SlackThreadReplyResponse(
                success=False, error="limit must be at least 1"
            )

        capped_limit = min(limit, 200)
        logger.info(
            "Fetching Slack thread replies channel=%s thread_ts=%s limit=%d",
            channel,
            thread_ts,
            capped_limit,
        )
        response = client.conversations_replies(
            channel=channel, ts=thread_ts, limit=capped_limit
        )

        msg_list: list[dict[str, Any]] = response.get("messages", [])
        messages = [
            MessageInfo(
                text=msg.get("text", ""),
                user=msg.get("user", "unknown"),
                timestamp=msg.get("ts", ""),
                channel=channel,
                thread_ts=msg.get("thread_ts"),
            )
            for msg in msg_list
        ]

        return SlackThreadReplyResponse(
            success=True,
            data=SlackThreadReplyData(
                messages=messages,
                count=len(messages),
                channel=channel,
                thread_ts=thread_ts,
            ),
        )
    except SlackApiError as e:
        logger.exception("Slack get_thread_replies failed")
        return SlackThreadReplyResponse(
            success=False, error=f"Slack API error: {e.response['error']}"
        )
    except Exception as e:
        logger.exception("Slack get_thread_replies failed")
        return SlackThreadReplyResponse(
            success=False, error=f"Failed to get Slack thread replies: {str(e)}"
        )


@tool()
async def slack_get_user_info(user_id: str) -> SlackUserInfoResponse:
    """Get profile information about a Slack user.

    Uses the users.info API method.

    Args:
        user_id: The Slack user ID (e.g., "U0123456789").

    Returns:
        Response containing the user's profile information.
    """
    try:
        client = _get_client()
        if client is None:
            return SlackUserInfoResponse(
                success=False,
                error="Slack not configured. Set SLACK_TOKEN environment variable.",
            )

        logger.info("Fetching Slack user info for user_id=%s", user_id)
        response = client.users_info(user=user_id)

        user_data: dict[str, Any] = response.get("user", {})
        profile: dict[str, Any] = user_data.get("profile", {})

        return SlackUserInfoResponse(
            success=True,
            data=SlackUserInfoData(
                user=SlackUserInfo(
                    id=user_data.get("id", user_id),
                    name=user_data.get("name", ""),
                    real_name=profile.get("real_name"),
                    email=profile.get("email"),
                    is_bot=user_data.get("is_bot"),
                    is_admin=user_data.get("is_admin"),
                ),
            ),
        )
    except SlackApiError as e:
        logger.exception("Slack get_user_info failed")
        return SlackUserInfoResponse(
            success=False, error=f"Slack API error: {e.response['error']}"
        )
    except Exception as e:
        logger.exception("Slack get_user_info failed")
        return SlackUserInfoResponse(
            success=False, error=f"Failed to get Slack user info: {str(e)}"
        )


@tool()
async def slack_list_channels() -> ListChannelsResponse:
    """List all channels in the Slack workspace.

    Uses the conversations.list API method. Returns both public and private
    channels the bot has access to.

    Returns:
        Response containing a list of channels with their IDs, names, and types.
    """
    try:
        client = _get_client()
        if client is None:
            return ListChannelsResponse(
                success=False,
                error="Slack not configured. Set SLACK_TOKEN environment variable.",
            )

        logger.info("Listing Slack channels")
        response = client.conversations_list()

        ch_list: list[dict[str, Any]] = response.get("channels", [])
        channels = [
            ChannelInfo(
                id=ch["id"],
                name=ch["name"],
                type="public" if not ch.get("is_private") else "private",
                is_member=ch.get("is_member"),
            )
            for ch in ch_list
        ]

        return ListChannelsResponse(
            success=True,
            data=ListChannelsData(channels=channels, count=len(channels)),
        )
    except SlackApiError as e:
        logger.exception("Slack list_channels failed")
        return ListChannelsResponse(
            success=False, error=f"Slack API error: {e.response['error']}"
        )
    except Exception as e:
        logger.exception("Slack list_channels failed")
        return ListChannelsResponse(
            success=False, error=f"Failed to list Slack channels: {str(e)}"
        )


@tool()
async def slack_get_channel_history(
    channel: str, limit: int = 100
) -> ChannelHistoryResponse:
    """Get the message history of a Slack channel.

    Uses the conversations.history API method.

    Args:
        channel: The channel ID to fetch history from.
        limit: The maximum number of messages to fetch (default 100, max 1000).

    Returns:
        Response containing the channel's message history.
    """
    try:
        client = _get_client()
        if client is None:
            return ChannelHistoryResponse(
                success=False,
                error="Slack not configured. Set SLACK_TOKEN environment variable.",
            )

        if limit < 1:
            return ChannelHistoryResponse(
                success=False, error="limit must be at least 1"
            )

        capped_limit = min(limit, 1000)
        logger.info(
            "Fetching Slack channel history channel=%s limit=%d", channel, capped_limit
        )
        response = client.conversations_history(channel=channel, limit=capped_limit)

        hist_list: list[dict[str, Any]] = response.get("messages", [])
        messages = [
            MessageInfo(
                text=msg.get("text", ""),
                user=msg.get("user", "unknown"),
                timestamp=msg.get("ts", ""),
                channel=channel,
                thread_ts=msg.get("thread_ts"),
            )
            for msg in hist_list
        ]

        return ChannelHistoryResponse(
            success=True,
            data=ChannelHistoryData(
                messages=messages, count=len(messages), channel=channel
            ),
        )
    except SlackApiError as e:
        logger.exception("Slack get_channel_history failed")
        return ChannelHistoryResponse(
            success=False, error=f"Slack API error: {e.response['error']}"
        )
    except Exception as e:
        logger.exception("Slack get_channel_history failed")
        return ChannelHistoryResponse(
            success=False, error=f"Failed to get channel history: {str(e)}"
        )


@tool()
async def slack_search_messages(query: str, limit: int = 20) -> SearchMessagesResponse:
    """Search messages across the Slack workspace.

    Uses the search.messages API method. Requires a user token with
    search:read scope (bot tokens cannot use search).

    Args:
        query: The search query. Supports modifiers like from:@user, in:#channel,
               has:link, has:reaction, before:YYYY-MM-DD, after:YYYY-MM-DD.
        limit: The maximum number of results to return (default 20, max 100).

    Returns:
        Response containing matching messages.
    """
    try:
        client = _get_client()
        if client is None:
            return SearchMessagesResponse(
                success=False,
                error="Slack not configured. Set SLACK_TOKEN environment variable.",
            )

        if limit < 1:
            return SearchMessagesResponse(
                success=False, error="limit must be at least 1"
            )

        capped_limit = min(limit, 100)
        logger.info(
            "Searching Slack messages query_length=%d limit=%d",
            len(query),
            capped_limit,
        )
        response = client.search_messages(query=query, count=capped_limit)

        matches: list[dict[str, Any]] = response.get("messages", {}).get("matches", [])  # type: ignore[call-overload]
        messages = [
            MessageInfo(
                text=msg.get("text", ""),
                user=msg.get("user", "unknown"),
                timestamp=msg.get("ts", ""),
                channel=msg.get("channel", {}).get("name", ""),
                permalink=msg.get("permalink", ""),
            )
            for msg in matches
        ]

        return SearchMessagesResponse(
            success=True,
            data=SearchMessagesData(
                messages=messages, count=len(messages), query=query
            ),
        )
    except SlackApiError as e:
        logger.exception("Slack search_messages failed")
        return SearchMessagesResponse(
            success=False, error=f"Slack API error: {e.response['error']}"
        )
    except Exception as e:
        logger.exception("Slack search_messages failed")
        return SearchMessagesResponse(
            success=False, error=f"Failed to search Slack messages: {str(e)}"
        )


@tool()
async def slack_reply_to_thread(
    channel: str, thread_ts: str, text: str, broadcast: bool = False
) -> SendMessageResponse:
    """Reply to a specific message thread in a Slack channel.

    Uses the chat.postMessage API method with thread_ts to post a threaded
    reply. This is a convenience wrapper that ensures the reply goes into an
    existing thread rather than starting a new conversation.

    Args:
        channel: The channel ID containing the parent message thread.
        thread_ts: The timestamp (ts) of the parent message to reply to.
                   This is the ts value from the original message that started
                   the thread.
        text: The text of the reply. Supports Slack mrkdwn formatting
              (e.g., *bold*, _italic_, ~strike~, `code`, ```code block```).
        broadcast: If true, the reply will also be posted to the channel as a
                   regular message, visible outside the thread. Known as
                   "Also send to channel" in the Slack UI.

    Returns:
        Response indicating success with message details, or an error.
    """
    try:
        client = _get_client()
        if client is None:
            return SendMessageResponse(
                success=False,
                error="Slack not configured. Set SLACK_TOKEN environment variable.",
            )

        if not thread_ts or not thread_ts.strip():
            return SendMessageResponse(
                success=False,
                error="thread_ts is required to reply in a thread.",
            )

        logger.info(
            "Replying to Slack thread channel=%s thread_ts=%s broadcast=%s",
            channel,
            thread_ts,
            broadcast,
        )
        kwargs: dict = {
            "channel": channel,
            "text": text,
            "thread_ts": thread_ts,
            "mrkdwn": True,
        }
        if broadcast:
            kwargs["reply_broadcast"] = True

        response = client.chat_postMessage(**kwargs)

        return SendMessageResponse(
            success=True,
            data=MessageSentData(
                message_id=response.get("ts"),
                channel=response.get("channel"),
                timestamp=response.get("ts"),
            ),
        )
    except SlackApiError as e:
        logger.exception("Slack reply_to_thread failed")
        return SendMessageResponse(
            success=False, error=f"Slack API error: {e.response['error']}"
        )
    except Exception as e:
        logger.exception("Slack reply_to_thread failed")
        return SendMessageResponse(
            success=False, error=f"Failed to reply to Slack thread: {str(e)}"
        )


@tool()
async def slack_set_channel_topic(
    channel: str, topic: str
) -> SlackSetChannelTopicResponse:
    """Set the topic of a Slack channel.

    Uses the conversations.setTopic API method. The bot must be a member of
    the channel and have the necessary permissions to change the topic.

    Args:
        channel: The channel ID to set the topic for.
        topic: The new topic text for the channel (up to 250 characters).

    Returns:
        Response indicating success with the updated topic, or an error.
    """
    try:
        client = _get_client()
        if client is None:
            return SlackSetChannelTopicResponse(
                success=False,
                error="Slack not configured. Set SLACK_TOKEN environment variable.",
            )

        if len(topic) > 250:
            return SlackSetChannelTopicResponse(
                success=False,
                error="Topic must be 250 characters or fewer.",
            )

        logger.info("Setting Slack channel topic channel=%s", channel)
        response = client.conversations_setTopic(channel=channel, topic=topic)

        return SlackSetChannelTopicResponse(
            success=True,
            data=SlackChannelTopicData(
                channel=response.get("channel", {}).get("id", channel),  # type: ignore[call-overload]
                topic=response.get("channel", {}).get("topic", {}).get("value", topic),  # type: ignore[call-overload]
            ),
        )
    except SlackApiError as e:
        logger.exception("Slack set_channel_topic failed")
        return SlackSetChannelTopicResponse(
            success=False, error=f"Slack API error: {e.response['error']}"
        )
    except Exception as e:
        logger.exception("Slack set_channel_topic failed")
        return SlackSetChannelTopicResponse(
            success=False, error=f"Failed to set Slack channel topic: {str(e)}"
        )
