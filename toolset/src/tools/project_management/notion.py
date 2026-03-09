"""Notion tools for page management, search, database queries, and block operations.

Uses the Notion API (version 2022-06-28). Requires a NOTION_API_KEY environment
variable (internal integration token).

API Reference: https://developers.notion.com/reference
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from src.humcp.decorator import tool
from src.tools.project_management.schemas import (
    NotionBlockData,
    NotionBlockListData,
    NotionBlockListResponse,
    NotionDatabaseQueryData,
    NotionDatabaseQueryResponse,
    NotionPageData,
    NotionPageListData,
    NotionPageListResponse,
    NotionPageResponse,
)

logger = logging.getLogger("humcp.tools.notion")

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _get_headers() -> tuple[dict[str, str] | None, str | None]:
    """Build Notion API headers from environment variables.

    Returns:
        A tuple of (headers_dict, error_message).
    """
    api_key = os.getenv("NOTION_API_KEY")
    if not api_key:
        return (
            None,
            "Notion API key not configured. Set NOTION_API_KEY environment variable.",
        )

    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }, None


def _extract_title(page: dict[str, Any]) -> str:
    """Extract the title from a Notion page properties dict.

    Args:
        page: The Notion page response dict.

    Returns:
        The page title string, or "Untitled".
    """
    properties = page.get("properties", {})

    # Try common title property names
    for prop_name in ("Name", "Title", "title"):
        prop = properties.get(prop_name, {})
        if prop.get("title") and len(prop["title"]) > 0:
            return prop["title"][0].get("text", {}).get("content", "Untitled")

    # Fall back to searching for any title-type property
    for prop in properties.values():
        if isinstance(prop, dict) and prop.get("type") == "title":
            title_list = prop.get("title", [])
            if title_list:
                return title_list[0].get("text", {}).get("content", "Untitled")

    return "Untitled"


def _extract_rich_text(rich_text_list: list[dict]) -> str:
    """Extract plain text from a Notion rich_text array.

    Args:
        rich_text_list: List of rich_text objects from the Notion API.

    Returns:
        Concatenated plain text content.
    """
    return "".join(item.get("text", {}).get("content", "") for item in rich_text_list)


def _page_to_data(page: dict[str, Any]) -> NotionPageData:
    """Convert a Notion page API response to NotionPageData.

    Args:
        page: Raw page dict from the Notion API.

    Returns:
        Parsed NotionPageData.
    """
    parent = page.get("parent", {})
    parent_id = parent.get("database_id") or parent.get("page_id")

    return NotionPageData(
        id=page["id"],
        title=_extract_title(page),
        url=page.get("url"),
        parent_id=parent_id,
        created_time=page.get("created_time"),
        last_edited_time=page.get("last_edited_time"),
    )


@tool()
async def notion_get_page(page_id: str) -> NotionPageResponse:
    """Retrieve a Notion page by its ID.

    Args:
        page_id: The ID of the Notion page to retrieve (UUID format, dashes optional).

    Returns:
        Page details including title, URL, parent, and timestamps.
    """
    try:
        headers, error = _get_headers()
        if error or headers is None:
            return NotionPageResponse(success=False, error=error)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{NOTION_API_BASE}/pages/{page_id}",
                headers=headers,
            )
            response.raise_for_status()
            page = response.json()

        data = _page_to_data(page)

        return NotionPageResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to get Notion page %s", page_id)
        return NotionPageResponse(success=False, error=f"Failed to get page: {e}")


@tool()
async def notion_create_page(
    parent_id: str,
    title: str,
    content: str = "",
    is_database: bool = False,
) -> NotionPageResponse:
    """Create a new page in Notion under a parent page or database.

    Args:
        parent_id: The ID of the parent page or database.
        title: The title of the new page.
        content: Optional text content for the page body.
        is_database: Set to True if parent_id is a database ID instead of a page ID.

    Returns:
        Details of the newly created page.
    """
    try:
        headers, error = _get_headers()
        if error or headers is None:
            return NotionPageResponse(success=False, error=error)

        if is_database:
            parent_obj: dict[str, str] = {"database_id": parent_id}
            title_prop = "Name"
        else:
            parent_obj = {"page_id": parent_id}
            title_prop = "title"

        payload: dict[str, Any] = {
            "parent": parent_obj,
            "properties": {
                title_prop: {
                    "title": [{"text": {"content": title}}],
                },
            },
        }

        children: list[dict[str, Any]] = []
        if content:
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}}],
                    },
                }
            )
            payload["children"] = children

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{NOTION_API_BASE}/pages",
                json=payload,
                headers=headers,
            )

            # If page_id parent fails and is_database was not set, retry with database_id
            if response.status_code == 400 and not is_database:
                payload["parent"] = {"database_id": parent_id}
                payload["properties"] = {
                    "Name": {
                        "title": [{"text": {"content": title}}],
                    },
                }
                response = await client.post(
                    f"{NOTION_API_BASE}/pages",
                    json=payload,
                    headers=headers,
                )

            response.raise_for_status()
            page = response.json()

        logger.info("Created Notion page '%s' (ID: %s)", title, page["id"])

        data = _page_to_data(page)

        return NotionPageResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to create Notion page '%s'", title)
        return NotionPageResponse(success=False, error=f"Failed to create page: {e}")


@tool()
async def notion_update_page(
    page_id: str,
    title: str | None = None,
    archived: bool | None = None,
) -> NotionPageResponse:
    """Update a Notion page's properties.

    Args:
        page_id: The ID of the page to update.
        title: New page title. Pass None to keep unchanged.
        archived: Set to True to archive the page, False to unarchive.

    Returns:
        Updated page details.
    """
    try:
        headers, error = _get_headers()
        if error or headers is None:
            return NotionPageResponse(success=False, error=error)

        payload: dict[str, Any] = {}

        if title is not None:
            # We need to find the title property name first
            async with httpx.AsyncClient(timeout=30.0) as client:
                get_resp = await client.get(
                    f"{NOTION_API_BASE}/pages/{page_id}",
                    headers=headers,
                )
                get_resp.raise_for_status()
                existing = get_resp.json()

            title_prop_name = "title"
            for prop_name, prop_val in existing.get("properties", {}).items():
                if isinstance(prop_val, dict) and prop_val.get("type") == "title":
                    title_prop_name = prop_name
                    break

            payload["properties"] = {
                title_prop_name: {
                    "title": [{"text": {"content": title}}],
                },
            }

        if archived is not None:
            payload["archived"] = archived

        if not payload:
            return NotionPageResponse(
                success=False, error="At least one field must be provided to update."
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                f"{NOTION_API_BASE}/pages/{page_id}",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            page = response.json()

        logger.info("Updated Notion page %s", page_id)

        data = _page_to_data(page)

        return NotionPageResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to update Notion page %s", page_id)
        return NotionPageResponse(success=False, error=f"Failed to update page: {e}")


@tool()
async def notion_search(
    query: str,
    page_size: int = 25,
) -> NotionPageListResponse:
    """Search for pages in Notion by title or content.

    Args:
        query: The search query string.
        page_size: Maximum number of results to return (max 100).

    Returns:
        List of pages matching the search query.
    """
    try:
        headers, error = _get_headers()
        if error or headers is None:
            return NotionPageListResponse(success=False, error=error)

        if page_size < 1:
            return NotionPageListResponse(
                success=False, error="page_size must be at least 1"
            )

        payload = {
            "query": query,
            "page_size": min(page_size, 100),
            "filter": {"value": "page", "property": "object"},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{NOTION_API_BASE}/search",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        pages = [_page_to_data(result) for result in data.get("results", [])]

        logger.info("Notion search returned %d results for: %s", len(pages), query)

        return NotionPageListResponse(
            success=True,
            data=NotionPageListData(
                pages=pages,
                total=len(pages),
                has_more=data.get("has_more", False),
                next_cursor=data.get("next_cursor"),
            ),
        )
    except Exception as e:
        logger.exception("Failed to search Notion for: %s", query)
        return NotionPageListResponse(success=False, error=f"Failed to search: {e}")


@tool()
async def notion_query_database(
    database_id: str,
    page_size: int = 25,
    start_cursor: str | None = None,
) -> NotionDatabaseQueryResponse:
    """Query a Notion database to retrieve its pages.

    Args:
        database_id: The ID of the Notion database to query.
        page_size: Maximum number of results to return (max 100).
        start_cursor: Optional cursor for pagination from a previous query.

    Returns:
        Pages in the database matching the query.
    """
    try:
        headers, error = _get_headers()
        if error or headers is None:
            return NotionDatabaseQueryResponse(success=False, error=error)

        if page_size < 1:
            return NotionDatabaseQueryResponse(
                success=False, error="page_size must be at least 1"
            )

        payload: dict[str, Any] = {
            "page_size": min(page_size, 100),
        }
        if start_cursor:
            payload["start_cursor"] = start_cursor

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{NOTION_API_BASE}/databases/{database_id}/query",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        pages = [_page_to_data(result) for result in data.get("results", [])]

        logger.info(
            "Notion database query returned %d results for database %s",
            len(pages),
            database_id,
        )

        return NotionDatabaseQueryResponse(
            success=True,
            data=NotionDatabaseQueryData(
                pages=pages,
                total=len(pages),
                has_more=data.get("has_more", False),
                next_cursor=data.get("next_cursor"),
            ),
        )
    except Exception as e:
        logger.exception("Failed to query Notion database %s", database_id)
        return NotionDatabaseQueryResponse(
            success=False, error=f"Failed to query database: {e}"
        )


@tool()
async def notion_get_block_children(
    block_id: str,
    page_size: int = 50,
    start_cursor: str | None = None,
) -> NotionBlockListResponse:
    """Get the children blocks of a Notion block or page. Useful for reading page content.

    Args:
        block_id: The ID of the block or page whose children to retrieve.
        page_size: Maximum number of blocks to return (max 100).
        start_cursor: Optional cursor for pagination.

    Returns:
        List of child blocks with their types and text content.
    """
    try:
        headers, error = _get_headers()
        if error or headers is None:
            return NotionBlockListResponse(success=False, error=error)

        if page_size < 1:
            return NotionBlockListResponse(
                success=False, error="page_size must be at least 1"
            )

        params: dict[str, Any] = {"page_size": min(page_size, 100)}
        if start_cursor:
            params["start_cursor"] = start_cursor

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{NOTION_API_BASE}/blocks/{block_id}/children",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        blocks = []
        for block in data.get("results", []):
            block_type = block.get("type", "unknown")
            content = None

            # Extract text content from common block types
            type_data = block.get(block_type, {})
            if isinstance(type_data, dict):
                rich_text = type_data.get("rich_text", [])
                if rich_text:
                    content = _extract_rich_text(rich_text)
                elif block_type == "child_page":
                    content = type_data.get("title", "")

            blocks.append(
                NotionBlockData(
                    id=block["id"],
                    block_type=block_type,
                    content=content,
                    has_children=block.get("has_children", False),
                )
            )

        logger.info("Retrieved %d blocks for Notion block %s", len(blocks), block_id)

        return NotionBlockListResponse(
            success=True,
            data=NotionBlockListData(
                blocks=blocks,
                total=len(blocks),
                has_more=data.get("has_more", False),
                next_cursor=data.get("next_cursor"),
            ),
        )
    except Exception as e:
        logger.exception("Failed to get blocks for Notion block %s", block_id)
        return NotionBlockListResponse(
            success=False, error=f"Failed to get blocks: {e}"
        )
