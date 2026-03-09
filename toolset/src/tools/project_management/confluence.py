"""Confluence wiki tools for page management, search, and space listing.

Uses the Atlassian Python API library. Requires CONFLUENCE_URL,
CONFLUENCE_USERNAME, and CONFLUENCE_API_TOKEN environment variables.

API Reference: https://developer.atlassian.com/cloud/confluence/rest/v2/
"""

from __future__ import annotations

import logging
import os

from src.humcp.decorator import tool
from src.tools.project_management.schemas import (
    ConfluenceCommentData,
    ConfluenceCommentListData,
    ConfluenceCommentListResponse,
    ConfluencePageData,
    ConfluencePageListData,
    ConfluencePageListResponse,
    ConfluencePageResponse,
    ConfluenceSpaceData,
    ConfluenceSpaceListData,
    ConfluenceSpaceListResponse,
)

try:
    from atlassian import Confluence
except ImportError as err:
    raise ImportError(
        "atlassian-python-api is required for Confluence tools. "
        "Install with: pip install atlassian-python-api"
    ) from err

logger = logging.getLogger("humcp.tools.confluence")


def _get_confluence_client() -> tuple[Confluence | None, str | None]:
    """Create a Confluence client from environment variables.

    Returns:
        A tuple of (client, error_message).
    """
    url = os.getenv("CONFLUENCE_URL")
    username = os.getenv("CONFLUENCE_USERNAME")
    api_token = os.getenv("CONFLUENCE_API_TOKEN")

    if not url:
        return (
            None,
            "Confluence URL not configured. Set CONFLUENCE_URL environment variable.",
        )
    if not username:
        return (
            None,
            "Confluence username not configured. Set CONFLUENCE_USERNAME environment variable.",
        )
    if not api_token:
        return (
            None,
            "Confluence API token not configured. Set CONFLUENCE_API_TOKEN environment variable.",
        )

    client = Confluence(url=url, username=username, password=api_token)
    return client, None


@tool()
async def confluence_get_page(page_id: str) -> ConfluencePageResponse:
    """Retrieve a Confluence page by its ID.

    Args:
        page_id: The ID of the Confluence page to retrieve.

    Returns:
        Page details including title, space key, body content (storage format HTML), version, and URL.
    """
    try:
        client, error = _get_confluence_client()
        if error or client is None:
            return ConfluencePageResponse(success=False, error=error)

        page = client.get_page_by_id(page_id, expand="body.storage,space,version")

        if not page:
            return ConfluencePageResponse(
                success=False,
                error=f"Page with ID {page_id} not found.",
            )

        body_content = None
        if page.get("body", {}).get("storage", {}).get("value"):
            body_content = page["body"]["storage"]["value"]

        space_key = page.get("space", {}).get("key")
        version_num = (
            page.get("version", {}).get("number") if page.get("version") else None
        )
        base_url = os.getenv("CONFLUENCE_URL", "")
        web_link = page.get("_links", {}).get("webui")
        page_url = (
            f"{base_url}{web_link}"
            if web_link and not web_link.startswith("http")
            else web_link
        )

        data = ConfluencePageData(
            id=page["id"],
            title=page["title"],
            space_key=space_key,
            body=body_content,
            version=version_num,
            url=page_url,
        )

        return ConfluencePageResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to get Confluence page %s", page_id)
        return ConfluencePageResponse(success=False, error=f"Failed to get page: {e}")


@tool()
async def confluence_create_page(
    space_key: str,
    title: str,
    body: str,
    parent_id: str | None = None,
) -> ConfluencePageResponse:
    """Create a new page in a Confluence space.

    Args:
        space_key: The key of the Confluence space (e.g., "DEV").
        title: The title of the new page.
        body: The HTML body content of the page (Confluence storage format).
        parent_id: Optional parent page ID for creating a child page.

    Returns:
        Details of the newly created page.
    """
    try:
        client, error = _get_confluence_client()
        if error or client is None:
            return ConfluencePageResponse(success=False, error=error)

        page = client.create_page(space_key, title, body, parent_id=parent_id)

        logger.info("Created Confluence page '%s' (ID: %s)", title, page["id"])

        base_url = os.getenv("CONFLUENCE_URL", "")
        web_link = page.get("_links", {}).get("webui")
        page_url = (
            f"{base_url}{web_link}"
            if web_link and not web_link.startswith("http")
            else web_link
        )

        data = ConfluencePageData(
            id=page["id"],
            title=title,
            space_key=space_key,
            version=1,
            url=page_url,
        )

        return ConfluencePageResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to create Confluence page '%s'", title)
        return ConfluencePageResponse(
            success=False, error=f"Failed to create page: {e}"
        )


@tool()
async def confluence_update_page(
    page_id: str,
    title: str,
    body: str,
) -> ConfluencePageResponse:
    """Update an existing Confluence page. Automatically increments the version number.

    Args:
        page_id: The ID of the page to update.
        title: The new page title.
        body: The new HTML body content (Confluence storage format).

    Returns:
        Details of the updated page.
    """
    try:
        client, error = _get_confluence_client()
        if error or client is None:
            return ConfluencePageResponse(success=False, error=error)

        page = client.update_page(page_id, title, body)

        logger.info("Updated Confluence page '%s' (ID: %s)", title, page_id)

        base_url = os.getenv("CONFLUENCE_URL", "")
        web_link = page.get("_links", {}).get("webui")
        page_url = (
            f"{base_url}{web_link}"
            if web_link and not web_link.startswith("http")
            else web_link
        )
        version_num = (
            page.get("version", {}).get("number") if page.get("version") else None
        )

        data = ConfluencePageData(
            id=str(page.get("id", page_id)),
            title=title,
            space_key=page.get("space", {}).get("key") if page.get("space") else None,
            version=version_num,
            url=page_url,
        )

        return ConfluencePageResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to update Confluence page %s", page_id)
        return ConfluencePageResponse(
            success=False, error=f"Failed to update page: {e}"
        )


@tool()
async def confluence_search(
    query: str,
    space_key: str | None = None,
    limit: int = 25,
) -> ConfluencePageListResponse:
    """Search for pages in Confluence using CQL (Confluence Query Language).

    Args:
        query: The search query string (text search or CQL expression).
        space_key: Optional space key to restrict search to a single space.
        limit: Maximum number of results to return (max 100).

    Returns:
        List of pages matching the search query.
    """
    try:
        client, error = _get_confluence_client()
        if error or client is None:
            return ConfluencePageListResponse(success=False, error=error)

        if limit < 1:
            return ConfluencePageListResponse(
                success=False, error="limit must be at least 1"
            )

        cql = f'text ~ "{query}"'
        if space_key:
            cql = f'{cql} AND space = "{space_key}"'

        results = client.cql(cql, limit=min(limit, 100))

        pages = []
        for result in results.get("results", []):
            content = result.get("content", result)
            pages.append(
                ConfluencePageData(
                    id=str(content.get("id", "")),
                    title=content.get("title", ""),
                    space_key=content.get("space", {}).get("key")
                    if isinstance(content.get("space"), dict)
                    else None,
                    url=content.get("_links", {}).get("webui"),
                )
            )

        logger.info("Confluence search returned %d results for: %s", len(pages), query)

        return ConfluencePageListResponse(
            success=True,
            data=ConfluencePageListData(
                pages=pages,
                total=results.get("totalSize", len(pages)),
            ),
        )
    except Exception as e:
        logger.exception("Failed to search Confluence for: %s", query)
        return ConfluencePageListResponse(success=False, error=f"Failed to search: {e}")


@tool()
async def confluence_list_spaces(
    limit: int = 25,
) -> ConfluenceSpaceListResponse:
    """List all Confluence spaces accessible to the authenticated user.

    Args:
        limit: Maximum number of spaces to return (max 100).

    Returns:
        List of Confluence spaces with their keys and names.
    """
    try:
        client, error = _get_confluence_client()
        if error or client is None:
            return ConfluenceSpaceListResponse(success=False, error=error)

        if limit < 1:
            return ConfluenceSpaceListResponse(
                success=False, error="limit must be at least 1"
            )

        result = client.get_all_spaces(limit=min(limit, 100))

        spaces_list = result.get("results", []) if isinstance(result, dict) else result

        spaces = [
            ConfluenceSpaceData(
                key=space.get("key", ""),
                name=space.get("name", ""),
                space_type=space.get("type"),
                url=space.get("_links", {}).get("webui"),
            )
            for space in spaces_list
        ]

        logger.info("Listed %d Confluence spaces", len(spaces))

        return ConfluenceSpaceListResponse(
            success=True,
            data=ConfluenceSpaceListData(spaces=spaces, total=len(spaces)),
        )
    except Exception as e:
        logger.exception("Failed to list Confluence spaces")
        return ConfluenceSpaceListResponse(
            success=False, error=f"Failed to list spaces: {e}"
        )


@tool()
async def confluence_get_page_comments(
    page_id: str,
    limit: int = 25,
) -> ConfluenceCommentListResponse:
    """Get comments on a Confluence page.

    Args:
        page_id: The ID of the Confluence page.
        limit: Maximum number of comments to return.

    Returns:
        List of comments on the page.
    """
    try:
        client, error = _get_confluence_client()
        if error or client is None:
            return ConfluenceCommentListResponse(success=False, error=error)

        if limit < 1:
            return ConfluenceCommentListResponse(
                success=False, error="limit must be at least 1"
            )

        result = client.get_page_comments(page_id, expand="body.storage", depth="all")

        comment_list = result.get("results", []) if isinstance(result, dict) else result

        comments = []
        for comment in comment_list[:limit]:
            body_text = comment.get("body", {}).get("storage", {}).get("value", "")
            author_name = None
            if comment.get("author"):
                author_name = comment["author"].get("displayName")

            comments.append(
                ConfluenceCommentData(
                    id=str(comment.get("id", "")),
                    body=body_text,
                    author=author_name,
                    created=comment.get("created"),
                )
            )

        logger.info("Listed %d comments for Confluence page %s", len(comments), page_id)

        return ConfluenceCommentListResponse(
            success=True,
            data=ConfluenceCommentListData(comments=comments, total=len(comments)),
        )
    except Exception as e:
        logger.exception("Failed to get comments for Confluence page %s", page_id)
        return ConfluenceCommentListResponse(
            success=False, error=f"Failed to get comments: {e}"
        )
