"""Zendesk tools for ticket management, search, and comments.

Uses the Zendesk Support API v2. Requires ZENDESK_SUBDOMAIN, ZENDESK_EMAIL,
and ZENDESK_API_TOKEN environment variables.

API Reference: https://developer.zendesk.com/api-reference/ticketing/
"""

from __future__ import annotations

import logging

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.project_management.schemas import (
    ZendeskCommentData,
    ZendeskCommentListData,
    ZendeskCommentListResponse,
    ZendeskTicketData,
    ZendeskTicketListData,
    ZendeskTicketListResponse,
    ZendeskTicketResponse,
)

logger = logging.getLogger("humcp.tools.zendesk")


async def _get_zendesk_config() -> tuple[
    str | None, str | None, tuple[str, str] | None, str | None
]:
    """Build Zendesk API configuration from environment variables.

    Returns:
        A tuple of (base_url, subdomain, auth_tuple, error_message).
    """
    subdomain = await resolve_credential("ZENDESK_SUBDOMAIN")
    email = await resolve_credential("ZENDESK_EMAIL")
    api_token = await resolve_credential("ZENDESK_API_TOKEN")

    if not subdomain:
        return (
            None,
            None,
            None,
            "Zendesk subdomain not configured. Set ZENDESK_SUBDOMAIN environment variable.",
        )
    if not email:
        return (
            None,
            None,
            None,
            "Zendesk email not configured. Set ZENDESK_EMAIL environment variable.",
        )
    if not api_token:
        return (
            None,
            None,
            None,
            "Zendesk API token not configured. Set ZENDESK_API_TOKEN environment variable.",
        )

    base_url = f"https://{subdomain}.zendesk.com/api/v2"
    # Zendesk uses email/token authentication
    auth = (f"{email}/token", api_token)

    return base_url, subdomain, auth, None


def _parse_ticket(ticket: dict, subdomain: str = "") -> ZendeskTicketData:
    """Parse a Zendesk ticket API response into ZendeskTicketData.

    Args:
        ticket: Raw ticket dict from the Zendesk API.
        subdomain: The Zendesk subdomain for constructing ticket URLs.

    Returns:
        Parsed ZendeskTicketData.
    """
    return ZendeskTicketData(
        id=ticket["id"],
        subject=ticket.get("subject", ""),
        description=ticket.get("description"),
        status=ticket.get("status"),
        priority=ticket.get("priority"),
        ticket_type=ticket.get("type"),
        assignee_id=ticket.get("assignee_id"),
        requester_id=ticket.get("requester_id"),
        tags=ticket.get("tags", []),
        url=f"https://{subdomain}.zendesk.com/agent/tickets/{ticket['id']}",
    )


@tool()
async def zendesk_create_ticket(
    subject: str,
    description: str,
    priority: str = "normal",
    ticket_type: str | None = None,
    tags: list[str] | None = None,
    assignee_id: int | None = None,
    requester_id: int | None = None,
) -> ZendeskTicketResponse:
    """Create a new ticket in Zendesk.

    Args:
        subject: The ticket subject line.
        description: The ticket description/body (first comment).
        priority: Ticket priority: "urgent", "high", "normal", or "low".
        ticket_type: Optional ticket type: "problem", "incident", "question", or "task".
        tags: Optional list of tags to apply to the ticket.
        assignee_id: Optional user ID to assign the ticket to.
        requester_id: Optional requester user ID.

    Returns:
        Details of the newly created ticket.
    """
    try:
        base_url, subdomain, auth, error = await _get_zendesk_config()
        if error or base_url is None or auth is None:
            return ZendeskTicketResponse(success=False, error=error)

        valid_priorities = ("urgent", "high", "normal", "low")
        if priority not in valid_priorities:
            return ZendeskTicketResponse(
                success=False,
                error=f"priority must be one of: {', '.join(valid_priorities)}",
            )

        ticket_data: dict = {
            "subject": subject,
            "comment": {"body": description},
            "priority": priority,
        }
        if ticket_type:
            valid_types = ("problem", "incident", "question", "task")
            if ticket_type not in valid_types:
                return ZendeskTicketResponse(
                    success=False,
                    error=f"ticket_type must be one of: {', '.join(valid_types)}",
                )
            ticket_data["type"] = ticket_type
        if tags:
            ticket_data["tags"] = tags
        if assignee_id is not None:
            ticket_data["assignee_id"] = assignee_id
        if requester_id is not None:
            ticket_data["requester_id"] = requester_id

        payload = {"ticket": ticket_data}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/tickets.json",
                json=payload,
                auth=auth,
            )
            response.raise_for_status()
            result = response.json()

        ticket = result.get("ticket", {})

        logger.info("Created Zendesk ticket #%s", ticket.get("id"))

        data = _parse_ticket(ticket, subdomain or "")

        return ZendeskTicketResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to create Zendesk ticket")
        return ZendeskTicketResponse(
            success=False, error=f"Failed to create ticket: {e}"
        )


@tool()
async def zendesk_get_ticket(ticket_id: int) -> ZendeskTicketResponse:
    """Retrieve a Zendesk ticket by its ID.

    Args:
        ticket_id: The numeric ID of the Zendesk ticket.

    Returns:
        Ticket details including subject, description, status, priority, type, and tags.
    """
    try:
        base_url, subdomain, auth, error = await _get_zendesk_config()
        if error or base_url is None or auth is None:
            return ZendeskTicketResponse(success=False, error=error)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/tickets/{ticket_id}.json",
                auth=auth,
            )
            response.raise_for_status()
            result = response.json()

        ticket = result.get("ticket", {})
        data = _parse_ticket(ticket, subdomain or "")

        return ZendeskTicketResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to get Zendesk ticket %d", ticket_id)
        return ZendeskTicketResponse(success=False, error=f"Failed to get ticket: {e}")


@tool()
async def zendesk_update_ticket(
    ticket_id: int,
    status: str | None = None,
    priority: str | None = None,
    assignee_id: int | None = None,
    tags: list[str] | None = None,
    subject: str | None = None,
    ticket_type: str | None = None,
    comment: str | None = None,
    comment_public: bool = True,
) -> ZendeskTicketResponse:
    """Update an existing Zendesk ticket. Optionally add a comment.

    Args:
        ticket_id: The numeric ID of the ticket to update.
        status: New status: "new", "open", "pending", "hold", "solved", or "closed".
        priority: New priority: "urgent", "high", "normal", or "low".
        assignee_id: New assignee user ID.
        tags: New list of tags (replaces existing tags).
        subject: New ticket subject.
        ticket_type: New ticket type: "problem", "incident", "question", or "task".
        comment: Optional comment body to add to the ticket.
        comment_public: Whether the comment is public (True) or internal (False).

    Returns:
        Updated ticket details.
    """
    try:
        base_url, subdomain, auth, error = await _get_zendesk_config()
        if error or base_url is None or auth is None:
            return ZendeskTicketResponse(success=False, error=error)

        ticket_data: dict = {}
        if status is not None:
            valid_statuses = ("new", "open", "pending", "hold", "solved", "closed")
            if status not in valid_statuses:
                return ZendeskTicketResponse(
                    success=False,
                    error=f"status must be one of: {', '.join(valid_statuses)}",
                )
            ticket_data["status"] = status
        if priority is not None:
            valid_priorities = ("urgent", "high", "normal", "low")
            if priority not in valid_priorities:
                return ZendeskTicketResponse(
                    success=False,
                    error=f"priority must be one of: {', '.join(valid_priorities)}",
                )
            ticket_data["priority"] = priority
        if assignee_id is not None:
            ticket_data["assignee_id"] = assignee_id
        if tags is not None:
            ticket_data["tags"] = tags
        if subject is not None:
            ticket_data["subject"] = subject
        if ticket_type is not None:
            ticket_data["type"] = ticket_type
        if comment is not None:
            ticket_data["comment"] = {"body": comment, "public": comment_public}

        if not ticket_data:
            return ZendeskTicketResponse(
                success=False, error="At least one field must be provided to update."
            )

        payload = {"ticket": ticket_data}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{base_url}/tickets/{ticket_id}.json",
                json=payload,
                auth=auth,
            )
            response.raise_for_status()
            result = response.json()

        ticket = result.get("ticket", {})

        logger.info("Updated Zendesk ticket #%d", ticket_id)

        data = _parse_ticket(ticket, subdomain or "")

        return ZendeskTicketResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to update Zendesk ticket %d", ticket_id)
        return ZendeskTicketResponse(
            success=False, error=f"Failed to update ticket: {e}"
        )


@tool()
async def zendesk_search_tickets(
    query: str,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    per_page: int = 25,
) -> ZendeskTicketListResponse:
    """Search for tickets in Zendesk using the Zendesk search syntax.

    Args:
        query: The search query string (Zendesk search syntax, e.g., "status:open priority:high").
        sort_by: Sort field: "created_at", "updated_at", "priority", "status", or "ticket_type".
        sort_order: Sort direction: "asc" or "desc".
        per_page: Maximum number of results to return (max 100).

    Returns:
        List of tickets matching the search query.
    """
    try:
        base_url, subdomain, auth, error = await _get_zendesk_config()
        if error or base_url is None or auth is None:
            return ZendeskTicketListResponse(success=False, error=error)

        if per_page < 1:
            return ZendeskTicketListResponse(
                success=False, error="per_page must be at least 1"
            )

        params = {
            "query": f"type:ticket {query}",
            "sort_by": sort_by,
            "sort_order": sort_order,
            "per_page": min(per_page, 100),
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/search.json",
                params=params,  # type: ignore[arg-type]
                auth=auth,
            )
            response.raise_for_status()
            result = response.json()

        tickets = [
            _parse_ticket(ticket, subdomain or "")
            for ticket in result.get("results", [])
        ]

        logger.info("Zendesk search returned %d tickets for: %s", len(tickets), query)

        return ZendeskTicketListResponse(
            success=True,
            data=ZendeskTicketListData(
                tickets=tickets,
                total=result.get("count", len(tickets)),
            ),
        )
    except Exception as e:
        logger.exception("Failed to search Zendesk tickets for: %s", query)
        return ZendeskTicketListResponse(
            success=False, error=f"Failed to search tickets: {e}"
        )


@tool()
async def zendesk_get_ticket_comments(
    ticket_id: int,
    per_page: int = 25,
) -> ZendeskCommentListResponse:
    """Get all comments on a Zendesk ticket.

    Args:
        ticket_id: The numeric ID of the ticket.
        per_page: Maximum number of comments to return (max 100).

    Returns:
        List of comments on the ticket, ordered chronologically.
    """
    try:
        base_url, _subdomain, auth, error = await _get_zendesk_config()
        if error or base_url is None or auth is None:
            return ZendeskCommentListResponse(success=False, error=error)

        if per_page < 1:
            return ZendeskCommentListResponse(
                success=False, error="per_page must be at least 1"
            )

        params = {"per_page": min(per_page, 100)}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/tickets/{ticket_id}/comments.json",
                params=params,
                auth=auth,
            )
            response.raise_for_status()
            result = response.json()

        comments = [
            ZendeskCommentData(
                id=comment["id"],
                body=comment.get("body", ""),
                author_id=comment.get("author_id"),
                public=comment.get("public", True),
                created_at=comment.get("created_at"),
            )
            for comment in result.get("comments", [])
        ]

        logger.info(
            "Retrieved %d comments for Zendesk ticket #%d", len(comments), ticket_id
        )

        return ZendeskCommentListResponse(
            success=True,
            data=ZendeskCommentListData(comments=comments, total=len(comments)),
        )
    except Exception as e:
        logger.exception("Failed to get comments for Zendesk ticket %d", ticket_id)
        return ZendeskCommentListResponse(
            success=False, error=f"Failed to get comments: {e}"
        )
