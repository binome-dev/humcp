"""Pydantic output schemas for Google Chat tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse


class ChatSpace(BaseModel):
    """Information about a Google Chat space."""

    name: str = Field(..., description="Space resource name")
    display_name: str = Field("", description="Display name of the space")
    type: str = Field("", description="Space type (ROOM, DIRECT_MESSAGE)")
    single_user_bot_dm: bool = Field(False, description="Whether this is a bot DM")
    threaded: bool = Field(False, description="Whether the space is threaded")


class ChatSpaceDetailed(BaseModel):
    """Detailed information about a Google Chat space."""

    name: str = Field(..., description="Space resource name")
    display_name: str = Field("", description="Display name of the space")
    type: str = Field("", description="Space type")
    single_user_bot_dm: bool = Field(False, description="Whether this is a bot DM")
    threaded: bool = Field(False, description="Whether the space is threaded")
    external_user_allowed: bool = Field(
        False, description="Whether external users allowed"
    )


class ChatMessage(BaseModel):
    """Information about a Google Chat message."""

    name: str = Field(..., description="Message resource name")
    text: str = Field("", description="Message text content")
    sender: str = Field("", description="Sender display name")
    sender_type: str = Field("", description="Sender type (HUMAN, BOT)")
    created: str = Field("", description="Creation time")
    thread_name: str = Field("", description="Thread resource name")


class ChatMessageDetailed(BaseModel):
    """Detailed information about a Google Chat message."""

    name: str = Field(..., description="Message resource name")
    text: str = Field("", description="Message text content")
    sender: str = Field("", description="Sender display name")
    sender_type: str = Field("", description="Sender type")
    created: str = Field("", description="Creation time")
    thread_name: str = Field("", description="Thread resource name")
    space_name: str = Field("", description="Space resource name")


class ChatSentMessage(BaseModel):
    """Information about a sent Google Chat message."""

    name: str = Field(..., description="Message resource name")
    text: str = Field("", description="Message text content")
    created: str = Field("", description="Creation time")
    thread_name: str = Field("", description="Thread resource name")


class ChatListSpacesData(BaseModel):
    """Output data for google_chat_list_spaces tool."""

    spaces: list[ChatSpace] = Field(..., description="List of spaces")
    total: int = Field(..., description="Total number of spaces")


class ChatGetMessagesData(BaseModel):
    """Output data for google_chat_get_messages tool."""

    messages: list[ChatMessage] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages")


# Chat Responses
class ChatListSpacesResponse(ToolResponse[ChatListSpacesData]):
    """Response for google_chat_list_spaces tool."""

    pass


class ChatGetSpaceResponse(ToolResponse[ChatSpaceDetailed]):
    """Response for google_chat_get_space tool."""

    pass


class ChatGetMessagesResponse(ToolResponse[ChatGetMessagesData]):
    """Response for google_chat_get_messages tool."""

    pass


class ChatGetMessageResponse(ToolResponse[ChatMessageDetailed]):
    """Response for google_chat_get_message tool."""

    pass


class ChatSendMessageResponse(ToolResponse[ChatSentMessage]):
    """Response for google_chat_send_message tool."""

    pass
