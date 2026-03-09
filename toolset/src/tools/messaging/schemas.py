"""Pydantic output schemas for messaging tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# Shared Messaging Schemas
# =============================================================================


class MessageSentData(BaseModel):
    """Data returned after sending a message."""

    message_id: str | None = Field(None, description="ID of the sent message")
    channel: str | None = Field(
        None, description="Channel or recipient the message was sent to"
    )
    timestamp: str | None = Field(None, description="Timestamp of the sent message")


class SendMessageResponse(ToolResponse[MessageSentData]):
    """Response schema for message-sending tools."""

    pass


# =============================================================================
# Channel / Room Listing Schemas
# =============================================================================


class ChannelInfo(BaseModel):
    """Information about a channel or room."""

    id: str = Field(..., description="Channel or room ID")
    name: str = Field(..., description="Channel or room name")
    type: str | None = Field(
        None, description="Channel type (e.g., public, private, direct)"
    )
    is_member: bool | None = Field(None, description="Whether the bot is a member")


class ListChannelsData(BaseModel):
    """Data returned when listing channels."""

    channels: list[ChannelInfo] = Field(..., description="List of channels")
    count: int = Field(..., description="Number of channels returned")


class ListChannelsResponse(ToolResponse[ListChannelsData]):
    """Response schema for channel-listing tools."""

    pass


# =============================================================================
# Message History Schemas
# =============================================================================


class MessageInfo(BaseModel):
    """A single message from channel history or search results."""

    text: str = Field(..., description="Message text content")
    user: str | None = Field(None, description="User who sent the message")
    timestamp: str | None = Field(None, description="Message timestamp")
    channel: str | None = Field(None, description="Channel the message belongs to")
    permalink: str | None = Field(None, description="Permalink to the message")
    thread_ts: str | None = Field(
        None, description="Thread timestamp if message is in a thread"
    )


class ChannelHistoryData(BaseModel):
    """Data returned when fetching channel history."""

    messages: list[MessageInfo] = Field(..., description="List of messages")
    count: int = Field(..., description="Number of messages returned")
    channel: str = Field(..., description="Channel ID the history was fetched from")


class ChannelHistoryResponse(ToolResponse[ChannelHistoryData]):
    """Response schema for channel history tools."""

    pass


# =============================================================================
# Search Messages Schemas
# =============================================================================


class SearchMessagesData(BaseModel):
    """Data returned when searching messages."""

    messages: list[MessageInfo] = Field(..., description="List of matching messages")
    count: int = Field(..., description="Number of matching messages")
    query: str = Field(..., description="The search query that was executed")


class SearchMessagesResponse(ToolResponse[SearchMessagesData]):
    """Response schema for message search tools."""

    pass


# =============================================================================
# Email Schemas
# =============================================================================


class EmailSentData(BaseModel):
    """Data returned after sending an email."""

    message_id: str | None = Field(None, description="ID of the sent email")
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")


class SendEmailResponse(ToolResponse[EmailSentData]):
    """Response schema for email-sending tools."""

    pass


# =============================================================================
# Batch Email Schemas (Resend)
# =============================================================================


class BatchEmailResultItem(BaseModel):
    """Result for a single email in a batch send."""

    id: str | None = Field(None, description="ID of the sent email")


class BatchEmailSentData(BaseModel):
    """Data returned after sending a batch of emails."""

    results: list[BatchEmailResultItem] = Field(..., description="List of send results")
    count: int = Field(..., description="Number of emails sent")


class BatchEmailSentResponse(ToolResponse[BatchEmailSentData]):
    """Response schema for batch email send."""

    pass


# =============================================================================
# SMS Schemas
# =============================================================================


class SmsSentData(BaseModel):
    """Data returned after sending an SMS."""

    message_sid: str | None = Field(None, description="SID of the sent SMS message")
    to: str = Field(..., description="Recipient phone number")
    from_number: str = Field(..., description="Sender phone number")
    status: str | None = Field(None, description="Message delivery status")


class SendSmsResponse(ToolResponse[SmsSentData]):
    """Response schema for SMS-sending tools."""

    pass


# =============================================================================
# SMS Status Schemas (Twilio)
# =============================================================================


class SmsStatusData(BaseModel):
    """Data returned when fetching SMS message status."""

    message_sid: str = Field(..., description="SID of the SMS message")
    to: str | None = Field(None, description="Recipient phone number")
    from_number: str | None = Field(None, description="Sender phone number")
    status: str | None = Field(
        None,
        description="Current message status (queued, sending, sent, delivered, failed, undelivered)",
    )
    date_sent: str | None = Field(None, description="Date the message was sent")
    error_code: int | None = Field(None, description="Error code if message failed")
    error_message: str | None = Field(
        None, description="Error message if message failed"
    )


class GetSmsStatusResponse(ToolResponse[SmsStatusData]):
    """Response schema for getting SMS message status."""

    pass


# =============================================================================
# Voice Call Schemas (Twilio)
# =============================================================================


class VoiceCallData(BaseModel):
    """Data returned after initiating a voice call."""

    call_sid: str | None = Field(None, description="SID of the initiated call")
    to: str = Field(..., description="Recipient phone number")
    from_number: str = Field(..., description="Caller phone number")
    status: str | None = Field(
        None, description="Call status (queued, ringing, in-progress, completed, etc.)"
    )


class MakeVoiceCallResponse(ToolResponse[VoiceCallData]):
    """Response schema for making a voice call."""

    pass


# =============================================================================
# Telegram Update Schemas
# =============================================================================


class TelegramUpdate(BaseModel):
    """A single Telegram update."""

    update_id: int = Field(..., description="Unique update identifier")
    message_text: str | None = Field(None, description="Text content of the message")
    chat_id: int | None = Field(None, description="Chat ID the update belongs to")
    from_user: str | None = Field(None, description="Username of the sender")
    date: int | None = Field(None, description="Unix timestamp of the message")


class TelegramUpdatesData(BaseModel):
    """Data returned when fetching Telegram updates."""

    updates: list[TelegramUpdate] = Field(..., description="List of updates")
    count: int = Field(..., description="Number of updates returned")


class TelegramUpdatesResponse(ToolResponse[TelegramUpdatesData]):
    """Response schema for Telegram get_updates tool."""

    pass


# =============================================================================
# Telegram Photo Schemas
# =============================================================================


class TelegramPhotoSentData(BaseModel):
    """Data returned after sending a photo via Telegram."""

    message_id: str | None = Field(None, description="ID of the sent photo message")
    chat_id: str | None = Field(None, description="Chat ID the photo was sent to")


class SendTelegramPhotoResponse(ToolResponse[TelegramPhotoSentData]):
    """Response schema for sending a Telegram photo."""

    pass


# =============================================================================
# Telegram Edit Message Schemas
# =============================================================================


class TelegramEditedMessageData(BaseModel):
    """Data returned after editing a Telegram message."""

    message_id: str | None = Field(None, description="ID of the edited message")
    chat_id: str | None = Field(None, description="Chat ID of the edited message")
    text: str | None = Field(None, description="New text of the edited message")


class EditTelegramMessageResponse(ToolResponse[TelegramEditedMessageData]):
    """Response schema for editing a Telegram message."""

    pass


# =============================================================================
# Discord Reaction Schemas
# =============================================================================


class ReactionAddedData(BaseModel):
    """Data returned after adding a reaction."""

    message_id: str = Field(
        ..., description="ID of the message the reaction was added to"
    )
    emoji: str = Field(..., description="The emoji that was added as a reaction")
    channel_id: str = Field(..., description="Channel ID of the message")


class AddReactionResponse(ToolResponse[ReactionAddedData]):
    """Response schema for adding a reaction."""

    pass


# =============================================================================
# Discord Get Messages Schemas
# =============================================================================


class DiscordMessageInfo(BaseModel):
    """A single Discord message."""

    id: str = Field(..., description="Message ID")
    content: str = Field(..., description="Message text content")
    author: str | None = Field(None, description="Author username")
    timestamp: str | None = Field(None, description="Message timestamp (ISO8601)")
    channel_id: str | None = Field(
        None, description="Channel the message was posted in"
    )


class GetMessagesData(BaseModel):
    """Data returned when fetching Discord messages."""

    messages: list[DiscordMessageInfo] = Field(..., description="List of messages")
    count: int = Field(..., description="Number of messages returned")
    channel_id: str = Field(
        ..., description="Channel ID the messages were fetched from"
    )


class GetMessagesResponse(ToolResponse[GetMessagesData]):
    """Response schema for fetching Discord messages."""

    pass


# =============================================================================
# Slack Reaction Schemas
# =============================================================================


class SlackReactionData(BaseModel):
    """Data returned after adding a Slack reaction."""

    channel: str = Field(..., description="Channel ID")
    timestamp: str = Field(
        ..., description="Message timestamp the reaction was added to"
    )
    reaction: str = Field(..., description="The reaction name that was added")


class SlackReactionResponse(ToolResponse[SlackReactionData]):
    """Response schema for Slack reaction tools."""

    pass


# =============================================================================
# Slack Thread Reply Schemas
# =============================================================================


class SlackThreadReplyData(BaseModel):
    """Data returned when fetching thread replies."""

    messages: list[MessageInfo] = Field(
        ..., description="List of messages in the thread"
    )
    count: int = Field(..., description="Number of messages in the thread")
    channel: str = Field(..., description="Channel ID")
    thread_ts: str = Field(..., description="Thread parent timestamp")


class SlackThreadReplyResponse(ToolResponse[SlackThreadReplyData]):
    """Response schema for Slack thread reply tools."""

    pass


# =============================================================================
# Slack User Info Schemas
# =============================================================================


class SlackUserInfo(BaseModel):
    """Information about a Slack user."""

    id: str = Field(..., description="User ID")
    name: str = Field(..., description="Username")
    real_name: str | None = Field(None, description="User's display name")
    email: str | None = Field(None, description="User's email address")
    is_bot: bool | None = Field(None, description="Whether the user is a bot")
    is_admin: bool | None = Field(None, description="Whether the user is an admin")


class SlackUserInfoData(BaseModel):
    """Data returned when fetching Slack user info."""

    user: SlackUserInfo = Field(..., description="User information")


class SlackUserInfoResponse(ToolResponse[SlackUserInfoData]):
    """Response schema for Slack user info tools."""

    pass


# =============================================================================
# Webex Room Schemas
# =============================================================================


class WebexRoomInfo(BaseModel):
    """Information about a Webex room."""

    id: str = Field(..., description="Room ID")
    title: str = Field(..., description="Room title")
    type: str | None = Field(None, description="Room type (direct, group)")
    is_locked: bool | None = Field(None, description="Whether the room is locked")
    created: str | None = Field(None, description="Room creation timestamp (ISO8601)")


class ListRoomsData(BaseModel):
    """Data returned when listing Webex rooms."""

    rooms: list[WebexRoomInfo] = Field(..., description="List of rooms")
    count: int = Field(..., description="Number of rooms returned")


class ListRoomsResponse(ToolResponse[ListRoomsData]):
    """Response schema for Webex room-listing tools."""

    pass


# =============================================================================
# Webex Create Room Schemas
# =============================================================================


class WebexRoomCreatedData(BaseModel):
    """Data returned after creating a Webex room."""

    id: str = Field(..., description="ID of the newly created room")
    title: str = Field(..., description="Title of the room")
    type: str | None = Field(None, description="Room type (direct, group)")
    created: str | None = Field(None, description="Room creation timestamp (ISO8601)")


class CreateRoomResponse(ToolResponse[WebexRoomCreatedData]):
    """Response schema for creating a Webex room."""

    pass


# =============================================================================
# Webex Room Details Schemas
# =============================================================================


class WebexRoomDetailsData(BaseModel):
    """Detailed data about a Webex room."""

    id: str = Field(..., description="Room ID")
    title: str = Field(..., description="Room title")
    type: str | None = Field(None, description="Room type (direct, group)")
    is_locked: bool | None = Field(None, description="Whether the room is locked")
    team_id: str | None = Field(None, description="Team ID if associated with a team")
    created: str | None = Field(None, description="Room creation timestamp (ISO8601)")
    creator_id: str | None = Field(None, description="ID of the room creator")


class GetRoomDetailsResponse(ToolResponse[WebexRoomDetailsData]):
    """Response schema for getting Webex room details."""

    pass


# =============================================================================
# WhatsApp Template Message Schemas
# =============================================================================


class WhatsAppTemplateSentData(BaseModel):
    """Data returned after sending a WhatsApp template message."""

    message_id: str | None = Field(None, description="ID of the sent template message")
    to: str = Field(..., description="Recipient phone number")
    template_name: str = Field(..., description="Name of the template used")


class SendWhatsAppTemplateResponse(ToolResponse[WhatsAppTemplateSentData]):
    """Response schema for sending a WhatsApp template message."""

    pass


# =============================================================================
# WhatsApp Media Message Schemas
# =============================================================================


class WhatsAppMediaSentData(BaseModel):
    """Data returned after sending a WhatsApp media message."""

    message_id: str | None = Field(None, description="ID of the sent media message")
    to: str = Field(..., description="Recipient phone number")
    media_type: str = Field(
        ..., description="Type of media sent (image, document, video, audio)"
    )


class SendWhatsAppMediaResponse(ToolResponse[WhatsAppMediaSentData]):
    """Response schema for sending a WhatsApp media message."""

    pass


# =============================================================================
# Slack Set Channel Topic Schemas
# =============================================================================


class SlackChannelTopicData(BaseModel):
    """Data returned after setting a Slack channel topic."""

    channel: str = Field(..., description="Channel ID the topic was set on")
    topic: str = Field(..., description="The new topic that was set")


class SlackSetChannelTopicResponse(ToolResponse[SlackChannelTopicData]):
    """Response schema for setting a Slack channel topic."""

    pass


# =============================================================================
# Discord Create Thread Schemas
# =============================================================================


class DiscordThreadCreatedData(BaseModel):
    """Data returned after creating a Discord thread."""

    thread_id: str = Field(..., description="ID of the newly created thread")
    name: str = Field(..., description="Name of the thread")
    channel_id: str = Field(
        ..., description="Parent channel ID the thread was created in"
    )
    type: str | None = Field(None, description="Thread type (e.g., public, private)")


class DiscordCreateThreadResponse(ToolResponse[DiscordThreadCreatedData]):
    """Response schema for creating a Discord thread."""

    pass


# =============================================================================
# Telegram Pin Message Schemas
# =============================================================================


class TelegramPinnedMessageData(BaseModel):
    """Data returned after pinning a Telegram message."""

    chat_id: str = Field(..., description="Chat ID where the message was pinned")
    message_id: int = Field(..., description="ID of the pinned message")


class TelegramPinMessageResponse(ToolResponse[TelegramPinnedMessageData]):
    """Response schema for pinning a Telegram message."""

    pass


# =============================================================================
# Twilio WhatsApp Schemas
# =============================================================================


class TwilioWhatsAppSentData(BaseModel):
    """Data returned after sending a WhatsApp message via Twilio."""

    message_sid: str | None = Field(
        None, description="SID of the sent WhatsApp message"
    )
    to: str = Field(..., description="Recipient WhatsApp number")
    from_number: str = Field(..., description="Sender WhatsApp number (Twilio)")
    status: str | None = Field(None, description="Message delivery status")


class TwilioSendWhatsAppResponse(ToolResponse[TwilioWhatsAppSentData]):
    """Response schema for sending a WhatsApp message via Twilio."""

    pass


# =============================================================================
# Generic Operation Success Schema
# =============================================================================


class OperationSuccessData(BaseModel):
    """Data returned for a generic successful operation."""

    message: str = Field(
        ..., description="Success message describing the completed operation"
    )


class OperationSuccessResponse(ToolResponse[OperationSuccessData]):
    """Response schema for generic success operations."""

    pass
