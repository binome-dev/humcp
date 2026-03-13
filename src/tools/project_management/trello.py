"""Trello project management tools for board, list, and card management.

Uses the Trello REST API v1. Requires TRELLO_API_KEY and TRELLO_TOKEN
environment variables.

API Reference: https://developer.atlassian.com/cloud/trello/rest/
"""

from __future__ import annotations

import logging

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.project_management.schemas import (
    TrelloBoardData,
    TrelloBoardListData,
    TrelloBoardListResponse,
    TrelloCardData,
    TrelloCardListData,
    TrelloCardListResponse,
    TrelloCardResponse,
    TrelloListData,
    TrelloListListData,
    TrelloListListResponse,
)

logger = logging.getLogger("humcp.tools.trello")

TRELLO_BASE_URL = "https://api.trello.com/1"


async def _get_auth_params() -> tuple[dict[str, str] | None, str | None]:
    """Build Trello authentication query parameters.

    Returns:
        A tuple of (params_dict, error_message).
    """
    api_key = await resolve_credential("TRELLO_API_KEY")
    token = await resolve_credential("TRELLO_TOKEN")

    if not api_key:
        return (
            None,
            "Trello API key not configured. Set TRELLO_API_KEY environment variable.",
        )
    if not token:
        return (
            None,
            "Trello token not configured. Set TRELLO_TOKEN environment variable.",
        )

    return {"key": api_key, "token": token}, None


def _parse_card(card: dict) -> TrelloCardData:
    """Parse a Trello card API response into TrelloCardData.

    Args:
        card: Raw card dict from the Trello API.

    Returns:
        Parsed TrelloCardData.
    """
    label_names = [
        label.get("name", label.get("color", ""))
        for label in card.get("labels", [])
        if label.get("name") or label.get("color")
    ]

    return TrelloCardData(
        id=card["id"],
        name=card["name"],
        description=card.get("desc"),
        url=card.get("url"),
        list_name=card.get("list", {}).get("name") if card.get("list") else None,
        labels=label_names,
        due=card.get("due"),
        closed=card.get("closed", False),
    )


@tool()
async def trello_create_card(
    list_id: str,
    name: str,
    description: str = "",
    due: str | None = None,
    label_ids: str | None = None,
    member_ids: str | None = None,
) -> TrelloCardResponse:
    """Create a new card in a Trello list.

    Args:
        list_id: The ID of the Trello list to add the card to.
        name: The name/title of the card.
        description: The description of the card (Markdown supported).
        due: Optional due date (ISO 8601 format, e.g., "2025-12-31T12:00:00.000Z").
        label_ids: Optional comma-separated label IDs to apply.
        member_ids: Optional comma-separated member IDs to assign.

    Returns:
        Details of the newly created card.
    """
    try:
        auth_params, error = await _get_auth_params()
        if error or auth_params is None:
            return TrelloCardResponse(success=False, error=error)

        params: dict = {
            **auth_params,
            "idList": list_id,
            "name": name,
            "desc": description,
        }
        if due:
            params["due"] = due
        if label_ids:
            params["idLabels"] = label_ids
        if member_ids:
            params["idMembers"] = member_ids

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{TRELLO_BASE_URL}/cards",
                params=params,
            )
            response.raise_for_status()
            card = response.json()

        data = _parse_card(card)

        logger.info("Created Trello card %s in list %s", card["id"], list_id)
        return TrelloCardResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to create Trello card in list %s", list_id)
        return TrelloCardResponse(success=False, error=f"Failed to create card: {e}")


@tool()
async def trello_get_card(card_id: str) -> TrelloCardResponse:
    """Get details of a specific Trello card.

    Args:
        card_id: The ID of the Trello card.

    Returns:
        Card details including name, description, labels, due date, and URL.
    """
    try:
        auth_params, error = await _get_auth_params()
        if error or auth_params is None:
            return TrelloCardResponse(success=False, error=error)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{TRELLO_BASE_URL}/cards/{card_id}",
                params=auth_params,
            )
            response.raise_for_status()
            card = response.json()

        data = _parse_card(card)

        return TrelloCardResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to get Trello card %s", card_id)
        return TrelloCardResponse(success=False, error=f"Failed to get card: {e}")


@tool()
async def trello_update_card(
    card_id: str,
    name: str | None = None,
    description: str | None = None,
    due: str | None = None,
    closed: bool | None = None,
    list_id: str | None = None,
) -> TrelloCardResponse:
    """Update an existing Trello card.

    Args:
        card_id: The ID of the card to update.
        name: New card name.
        description: New card description.
        due: New due date (ISO 8601 format) or empty string to remove.
        closed: Set to True to archive the card, False to unarchive.
        list_id: New list ID to move the card to.

    Returns:
        Updated card details.
    """
    try:
        auth_params, error = await _get_auth_params()
        if error or auth_params is None:
            return TrelloCardResponse(success=False, error=error)

        params: dict = {**auth_params}
        if name is not None:
            params["name"] = name
        if description is not None:
            params["desc"] = description
        if due is not None:
            params["due"] = due
        if closed is not None:
            params["closed"] = str(closed).lower()
        if list_id is not None:
            params["idList"] = list_id

        if len(params) == len(auth_params):
            return TrelloCardResponse(
                success=False, error="At least one field must be provided to update."
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{TRELLO_BASE_URL}/cards/{card_id}",
                params=params,
            )
            response.raise_for_status()
            card = response.json()

        data = _parse_card(card)

        logger.info("Updated Trello card %s", card_id)
        return TrelloCardResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to update Trello card %s", card_id)
        return TrelloCardResponse(success=False, error=f"Failed to update card: {e}")


@tool()
async def trello_get_board_cards(
    board_id: str,
) -> TrelloCardListResponse:
    """Get all cards on a Trello board.

    Args:
        board_id: The ID of the Trello board.

    Returns:
        List of all cards on the board.
    """
    try:
        auth_params, error = await _get_auth_params()
        if error or auth_params is None:
            return TrelloCardListResponse(success=False, error=error)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{TRELLO_BASE_URL}/boards/{board_id}/cards",
                params=auth_params,
            )
            response.raise_for_status()
            cards_json = response.json()

        cards = [_parse_card(card) for card in cards_json]

        logger.info("Retrieved %d cards from Trello board %s", len(cards), board_id)

        return TrelloCardListResponse(
            success=True,
            data=TrelloCardListData(cards=cards, total=len(cards)),
        )
    except Exception as e:
        logger.exception("Failed to get cards for Trello board %s", board_id)
        return TrelloCardListResponse(success=False, error=f"Failed to get cards: {e}")


@tool()
async def trello_get_boards() -> TrelloBoardListResponse:
    """Get all boards accessible to the authenticated Trello user.

    Returns:
        List of Trello boards with their details.
    """
    try:
        auth_params, error = await _get_auth_params()
        if error or auth_params is None:
            return TrelloBoardListResponse(success=False, error=error)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{TRELLO_BASE_URL}/members/me/boards",
                params=auth_params,
            )
            response.raise_for_status()
            boards_json = response.json()

        boards = [
            TrelloBoardData(
                id=board["id"],
                name=board["name"],
                description=board.get("desc"),
                url=board.get("url"),
                closed=board.get("closed", False),
            )
            for board in boards_json
        ]

        logger.info("Retrieved %d Trello boards", len(boards))

        return TrelloBoardListResponse(
            success=True,
            data=TrelloBoardListData(boards=boards, total=len(boards)),
        )
    except Exception as e:
        logger.exception("Failed to get Trello boards")
        return TrelloBoardListResponse(
            success=False, error=f"Failed to get boards: {e}"
        )


@tool()
async def trello_get_board_lists(
    board_id: str,
) -> TrelloListListResponse:
    """Get all lists on a Trello board.

    Args:
        board_id: The ID of the Trello board.

    Returns:
        List of lists (columns) on the board.
    """
    try:
        auth_params, error = await _get_auth_params()
        if error or auth_params is None:
            return TrelloListListResponse(success=False, error=error)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{TRELLO_BASE_URL}/boards/{board_id}/lists",
                params=auth_params,
            )
            response.raise_for_status()
            lists_json = response.json()

        lists = [
            TrelloListData(
                id=lst["id"],
                name=lst["name"],
                closed=lst.get("closed", False),
            )
            for lst in lists_json
        ]

        logger.info("Retrieved %d lists from Trello board %s", len(lists), board_id)

        return TrelloListListResponse(
            success=True,
            data=TrelloListListData(lists=lists, total=len(lists)),
        )
    except Exception as e:
        logger.exception("Failed to get lists for Trello board %s", board_id)
        return TrelloListListResponse(success=False, error=f"Failed to get lists: {e}")
