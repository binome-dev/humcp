"""Google Gmail tools for searching, reading, and sending emails."""

import asyncio
import base64
import logging
from email.mime.text import MIMEText

from src.humcp.decorator import tool
from src.tools.google.auth import SCOPES, get_google_service
from src.tools.google.schemas import (
    GmailLabel,
    GmailLabelsData,
    GmailLabelsResponse,
    GmailMessageFull,
    GmailReadResponse,
    GmailSearchData,
    GmailSearchResponse,
    GmailSendData,
    GmailSendResponse,
    GmailThread,
    GmailThreadsData,
    GmailThreadsResponse,
)

logger = logging.getLogger("humcp.tools.google.gmail")

# Scopes required for Gmail operations
GMAIL_READONLY_SCOPES = [SCOPES["gmail_readonly"]]
GMAIL_SEND_SCOPES = [SCOPES["gmail_send"]]


@tool()
async def google_gmail_search(
    query: str = "", max_results: int = 10
) -> GmailSearchResponse:
    """Search Gmail messages.

    Searches for emails matching the query using Gmail's search syntax.
    Examples: "from:john@example.com", "subject:meeting", "is:unread".

    Args:
        query: Gmail search query (default: "" returns recent emails).
        max_results: Maximum number of messages to return (default: 10, max: 100).

    Returns:
        List of messages with id, thread_id, subject, from, to, date, and snippet.
    """
    capped_results = min(max_results, 100)

    try:

        def _search():
            service = get_google_service("gmail", "v1", GMAIL_READONLY_SCOPES)
            results = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=capped_results)
                .execute()
            )

            messages = results.get("messages", [])
            if not messages:
                return []

            detailed = []
            for msg in messages:
                msg_data = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="metadata")
                    .execute()
                )
                headers = {
                    h["name"].lower(): h["value"]
                    for h in msg_data.get("payload", {}).get("headers", [])
                }
                detailed.append(
                    {
                        "id": msg["id"],
                        "thread_id": msg_data.get("threadId"),
                        "subject": headers.get("subject", "(no subject)"),
                        "from": headers.get("from", ""),
                        "to": headers.get("to", ""),
                        "date": headers.get("date", ""),
                        "snippet": msg_data.get("snippet", ""),
                    }
                )

            return detailed

        logger.info("gmail_search query=%s max_results=%s", query, capped_results)
        messages = await asyncio.to_thread(_search)
        return GmailSearchResponse(
            success=True,
            data=GmailSearchData(messages=messages, total=len(messages)),
        )
    except Exception as e:
        logger.exception("gmail_search failed")
        return GmailSearchResponse(success=False, error=str(e))


@tool()
async def google_gmail_read(message_id: str) -> GmailReadResponse:
    """Read the full content of a Gmail message.

    Retrieves the complete email including headers, body text, and labels.

    Args:
        message_id: ID of the message to read.

    Returns:
        Full message with id, thread_id, subject, from, to, cc, date, body, and labels.
    """
    try:

        def _read():
            service = get_google_service("gmail", "v1", GMAIL_READONLY_SCOPES)
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            headers = {
                h["name"].lower(): h["value"]
                for h in msg.get("payload", {}).get("headers", [])
            }

            body = ""
            payload = msg.get("payload", {})

            if "body" in payload and payload["body"].get("data"):
                body = base64.urlsafe_b64decode(payload["body"]["data"]).decode()
            elif "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain":
                        if part.get("body", {}).get("data"):
                            body = base64.urlsafe_b64decode(
                                part["body"]["data"]
                            ).decode()
                            break
                    elif part.get("mimeType") == "text/html" and not body:
                        if part.get("body", {}).get("data"):
                            body = base64.urlsafe_b64decode(
                                part["body"]["data"]
                            ).decode()

            return GmailMessageFull(
                id=msg["id"],
                thread_id=msg.get("threadId"),
                subject=headers.get("subject", "(no subject)"),
                from_=headers.get("from", ""),
                to=headers.get("to", ""),
                cc=headers.get("cc", ""),
                date=headers.get("date", ""),
                body=body,
                labels=msg.get("labelIds", []),
            )

        logger.info("gmail_read message_id=%s", message_id)
        result = await asyncio.to_thread(_read)
        return GmailReadResponse(success=True, data=result)
    except Exception as e:
        logger.exception("gmail_read failed")
        return GmailReadResponse(success=False, error=str(e))


@tool()
async def google_gmail_send(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
) -> GmailSendResponse:
    """Send an email via Gmail.

    Composes and sends an email to the specified recipients.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain text email body.
        cc: Optional CC recipients (comma-separated).
        bcc: Optional BCC recipients (comma-separated).

    Returns:
        Sent message details with message_id and thread_id.
    """
    try:

        def _send():
            service = get_google_service("gmail", "v1", GMAIL_SEND_SCOPES)

            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            if cc:
                message["cc"] = cc
            if bcc:
                message["bcc"] = bcc

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            result = (
                service.users()
                .messages()
                .send(userId="me", body={"raw": raw})
                .execute()
            )

            return GmailSendData(
                message_id=result.get("id"),
                thread_id=result.get("threadId"),
            )

        logger.info("gmail_send to=%s subject=%s", to, subject)
        result = await asyncio.to_thread(_send)
        return GmailSendResponse(success=True, data=result)
    except Exception as e:
        logger.exception("gmail_send failed")
        return GmailSendResponse(success=False, error=str(e))


@tool()
async def google_gmail_labels() -> GmailLabelsResponse:
    """List all Gmail labels.

    Returns all labels in the user's mailbox including system labels
    (INBOX, SENT, etc.) and user-created labels.

    Returns:
        List of labels with id and name.
    """
    try:

        def _list_labels():
            service = get_google_service("gmail", "v1", GMAIL_READONLY_SCOPES)
            results = service.users().labels().list(userId="me").execute()
            items = results.get("labels", [])
            return [GmailLabel(id=label["id"], name=label["name"]) for label in items]

        logger.info("gmail_labels")
        labels = await asyncio.to_thread(_list_labels)
        return GmailLabelsResponse(
            success=True,
            data=GmailLabelsData(labels=labels, total=len(labels)),
        )
    except Exception as e:
        logger.exception("gmail_labels failed")
        return GmailLabelsResponse(success=False, error=str(e))


@tool()
async def google_gmail_list_threads(
    query: str = "",
    max_results: int = 20,
) -> GmailThreadsResponse:
    """List Gmail threads (conversation groups).

    Returns threads matching the query, ordered by most recent first.
    Each thread groups related messages into a single conversation.

    Args:
        query: Gmail search query to filter threads (default: "" returns recent threads).
        max_results: Maximum number of threads to return (default: 20, max: 100).

    Returns:
        List of threads with id, snippet, message_count, subject, and last_date.
    """
    capped_results = min(max_results, 100)

    try:

        def _list_threads():
            service = get_google_service("gmail", "v1", GMAIL_READONLY_SCOPES)
            results = (
                service.users()
                .threads()
                .list(userId="me", q=query, maxResults=capped_results)
                .execute()
            )

            thread_list = results.get("threads", [])
            estimated_total = results.get("resultSizeEstimate")

            threads = []
            for t in thread_list:
                thread_data = (
                    service.users()
                    .threads()
                    .get(userId="me", id=t["id"], format="metadata")
                    .execute()
                )
                messages = thread_data.get("messages", [])

                subject = ""
                last_date = ""
                if messages:
                    first_msg_headers = {
                        h["name"].lower(): h["value"]
                        for h in messages[0].get("payload", {}).get("headers", [])
                    }
                    subject = first_msg_headers.get("subject", "")

                    last_msg_headers = {
                        h["name"].lower(): h["value"]
                        for h in messages[-1].get("payload", {}).get("headers", [])
                    }
                    last_date = last_msg_headers.get("date", "")

                threads.append(
                    GmailThread(
                        id=thread_data["id"],
                        snippet=thread_data.get("snippet", ""),
                        history_id=thread_data.get("historyId"),
                        message_count=len(messages),
                        subject=subject,
                        last_date=last_date,
                    )
                )

            return threads, estimated_total

        logger.info("gmail_list_threads query=%s max_results=%s", query, capped_results)
        threads, estimated_total = await asyncio.to_thread(_list_threads)
        return GmailThreadsResponse(
            success=True,
            data=GmailThreadsData(
                threads=threads,
                total=len(threads),
                estimated_total=estimated_total,
            ),
        )
    except Exception as e:
        logger.exception("gmail_list_threads failed")
        return GmailThreadsResponse(success=False, error=str(e))
