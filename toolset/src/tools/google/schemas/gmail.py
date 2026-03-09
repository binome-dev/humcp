"""Pydantic output schemas for Gmail tools."""

from typing import Any

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse


class GmailMessage(BaseModel):
    """Summary of a Gmail message."""

    id: str = Field(..., description="Message ID")
    thread_id: str | None = Field(None, description="Thread ID")
    subject: str = Field(..., description="Email subject")
    from_: str = Field("", alias="from", description="Sender address")
    to: str = Field("", description="Recipient address")
    date: str = Field("", description="Date sent")
    snippet: str = Field("", description="Message preview snippet")


class GmailMessageFull(BaseModel):
    """Full Gmail message content."""

    id: str = Field(..., description="Message ID")
    thread_id: str | None = Field(None, description="Thread ID")
    subject: str = Field(..., description="Email subject")
    from_: str = Field("", alias="from", description="Sender address")
    to: str = Field("", description="Recipient address")
    cc: str = Field("", description="CC recipients")
    date: str = Field("", description="Date sent")
    body: str = Field("", description="Message body text")
    labels: list[str] = Field(default_factory=list, description="Gmail labels")


class GmailSearchData(BaseModel):
    """Output data for google_gmail_search tool."""

    messages: list[dict[str, Any]] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages")


class GmailSendData(BaseModel):
    """Output data for google_gmail_send tool."""

    message_id: str | None = Field(None, description="Sent message ID")
    thread_id: str | None = Field(None, description="Thread ID")


class GmailLabel(BaseModel):
    """Gmail label information."""

    id: str = Field(..., description="Label ID")
    name: str = Field(..., description="Label name")


class GmailLabelsData(BaseModel):
    """Output data for google_gmail_labels tool."""

    labels: list[GmailLabel] = Field(..., description="List of labels")
    total: int = Field(..., description="Total number of labels")


class GmailThread(BaseModel):
    """Summary of a Gmail thread."""

    id: str = Field(..., description="Thread ID")
    snippet: str = Field("", description="Thread preview snippet")
    history_id: str | None = Field(None, description="History ID")
    message_count: int = Field(0, description="Number of messages in the thread")
    subject: str = Field("", description="Thread subject from first message")
    last_date: str = Field("", description="Date of most recent message")


class GmailThreadsData(BaseModel):
    """Output data for google_gmail_list_threads tool."""

    threads: list[GmailThread] = Field(..., description="List of threads")
    total: int = Field(..., description="Total number of threads returned")
    estimated_total: int | None = Field(
        None, description="Estimated total threads matching the query"
    )


# Gmail Responses
class GmailSearchResponse(ToolResponse[GmailSearchData]):
    """Response for google_gmail_search tool."""

    pass


class GmailReadResponse(ToolResponse[GmailMessageFull]):
    """Response for google_gmail_read tool."""

    pass


class GmailSendResponse(ToolResponse[GmailSendData]):
    """Response for google_gmail_send tool."""

    pass


class GmailLabelsResponse(ToolResponse[GmailLabelsData]):
    """Response for google_gmail_labels tool."""

    pass


class GmailThreadsResponse(ToolResponse[GmailThreadsData]):
    """Response for google_gmail_list_threads tool."""

    pass
