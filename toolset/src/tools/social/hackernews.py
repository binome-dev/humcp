"""Hacker News tools for browsing top stories and searching via Algolia."""

from __future__ import annotations

import logging

import httpx

from src.humcp.decorator import tool
from src.tools.social.schemas import (
    HackerNewsComment,
    HackerNewsCommentsData,
    HackerNewsCommentsResponse,
    HackerNewsSearchByDateResponse,
    HackerNewsSearchData,
    HackerNewsSearchResponse,
    HackerNewsSearchResult,
    HackerNewsStory,
    HackerNewsStoryData,
    HackerNewsStoryResponse,
    HackerNewsTopStoriesData,
    HackerNewsTopStoriesResponse,
    HackerNewsUser,
    HackerNewsUserData,
    HackerNewsUserResponse,
)

logger = logging.getLogger("humcp.tools.hackernews")

_HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
_ALGOLIA_API_BASE = "https://hn.algolia.com/api/v1"


@tool()
async def hackernews_get_top_stories(
    limit: int = 10,
) -> HackerNewsTopStoriesResponse:
    """Get the current top stories from Hacker News.

    Args:
        limit: Maximum number of stories to return (default 10, max 50).

    Returns:
        Top stories or an error message.
    """
    try:
        limit = max(1, min(limit, 50))
        logger.info("HN get top stories limit=%d", limit)

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{_HN_API_BASE}/topstories.json")
            response.raise_for_status()
            story_ids: list[int] = response.json()

            stories: list[HackerNewsStory] = []
            for story_id in story_ids[:limit]:
                item_resp = await client.get(f"{_HN_API_BASE}/item/{story_id}.json")
                item_resp.raise_for_status()
                item = item_resp.json()
                if item is None:
                    continue

                stories.append(
                    HackerNewsStory(
                        id=item["id"],
                        title=item.get("title", ""),
                        url=item.get("url"),
                        score=item.get("score", 0),
                        by=item.get("by", "unknown"),
                        time=item.get("time", 0),
                        descendants=item.get("descendants", 0),
                        type=item.get("type", "story"),
                    )
                )

        logger.info("HN top stories complete results=%d", len(stories))
        return HackerNewsTopStoriesResponse(
            success=True,
            data=HackerNewsTopStoriesData(stories=stories),
        )
    except Exception as e:
        logger.exception("HN get top stories failed")
        return HackerNewsTopStoriesResponse(
            success=False, error=f"Hacker News top stories failed: {e}"
        )


@tool()
async def hackernews_get_story(story_id: int) -> HackerNewsStoryResponse:
    """Get a specific Hacker News story by its ID.

    Args:
        story_id: The numeric Hacker News item ID.

    Returns:
        The story details or an error message.
    """
    try:
        logger.info("HN get story id=%d", story_id)

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{_HN_API_BASE}/item/{story_id}.json")
            response.raise_for_status()
            item = response.json()

        if item is None:
            return HackerNewsStoryResponse(
                success=False,
                error=f"Story with ID {story_id} not found.",
            )

        story = HackerNewsStory(
            id=item["id"],
            title=item.get("title", ""),
            url=item.get("url"),
            score=item.get("score", 0),
            by=item.get("by", "unknown"),
            time=item.get("time", 0),
            descendants=item.get("descendants", 0),
            type=item.get("type", "story"),
        )

        return HackerNewsStoryResponse(
            success=True,
            data=HackerNewsStoryData(story=story),
        )
    except Exception as e:
        logger.exception("HN get story failed")
        return HackerNewsStoryResponse(
            success=False, error=f"Hacker News get story failed: {e}"
        )


@tool()
async def hackernews_search(
    query: str,
    limit: int = 10,
) -> HackerNewsSearchResponse:
    """Search Hacker News stories using the Algolia HN Search API.

    Args:
        query: The search query string.
        limit: Maximum number of results to return (default 10, max 50).

    Returns:
        Matching stories or an error message.
    """
    try:
        limit = max(1, min(limit, 50))
        logger.info("HN search query=%r limit=%d", query, limit)

        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": limit,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_ALGOLIA_API_BASE}/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        results: list[HackerNewsSearchResult] = []
        for hit in data.get("hits", []):
            results.append(
                HackerNewsSearchResult(
                    objectID=hit.get("objectID", ""),
                    title=hit.get("title", ""),
                    url=hit.get("url"),
                    points=hit.get("points"),
                    author=hit.get("author"),
                    created_at=hit.get("created_at"),
                    num_comments=hit.get("num_comments"),
                )
            )

        logger.info("HN search complete results=%d", len(results))
        return HackerNewsSearchResponse(
            success=True,
            data=HackerNewsSearchData(
                query=query,
                results=results,
            ),
        )
    except Exception as e:
        logger.exception("HN search failed")
        return HackerNewsSearchResponse(
            success=False, error=f"Hacker News search failed: {e}"
        )


@tool()
async def hackernews_search_by_date(
    query: str,
    tags: str = "story",
    limit: int = 10,
) -> HackerNewsSearchByDateResponse:
    """Search Hacker News stories sorted by date (most recent first) using the Algolia API.

    Unlike hackernews_search which sorts by relevance, this returns results
    ordered by creation date, making it useful for finding the latest discussions.

    Args:
        query: The search query string.
        tags: Filter by item type. Options: "story", "comment", "show_hn", "ask_hn", "front_page". Can combine with comma: "story,show_hn". Default is "story".
        limit: Maximum number of results to return (default 10, max 50).

    Returns:
        Matching items sorted by date (newest first) or an error message.
    """
    try:
        limit = max(1, min(limit, 50))
        logger.info("HN search_by_date query=%r tags=%s limit=%d", query, tags, limit)

        params = {
            "query": query,
            "tags": tags,
            "hitsPerPage": limit,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_ALGOLIA_API_BASE}/search_by_date",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        results: list[HackerNewsSearchResult] = []
        for hit in data.get("hits", []):
            results.append(
                HackerNewsSearchResult(
                    objectID=hit.get("objectID", ""),
                    title=hit.get("title", ""),
                    url=hit.get("url"),
                    points=hit.get("points"),
                    author=hit.get("author"),
                    created_at=hit.get("created_at"),
                    num_comments=hit.get("num_comments"),
                )
            )

        logger.info("HN search_by_date complete results=%d", len(results))
        return HackerNewsSearchByDateResponse(
            success=True,
            data=HackerNewsSearchData(
                query=query,
                results=results,
            ),
        )
    except Exception as e:
        logger.exception("HN search_by_date failed")
        return HackerNewsSearchByDateResponse(
            success=False, error=f"Hacker News search by date failed: {e}"
        )


@tool()
async def hackernews_get_user(username: str) -> HackerNewsUserResponse:
    """Get a Hacker News user profile by username.

    Returns the user's karma, bio, account creation date, and recent submission IDs.

    Args:
        username: The Hacker News username (case-sensitive).

    Returns:
        User profile details or an error message.
    """
    try:
        logger.info("HN get user username=%s", username)

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{_HN_API_BASE}/user/{username}.json")
            response.raise_for_status()
            item = response.json()

        if item is None:
            return HackerNewsUserResponse(
                success=False,
                error=f"User '{username}' not found.",
            )

        user = HackerNewsUser(
            id=item.get("id", username),
            created=item.get("created", 0),
            karma=item.get("karma", 0),
            about=item.get("about"),
            submitted=item.get("submitted", [])[:100],
        )

        return HackerNewsUserResponse(
            success=True,
            data=HackerNewsUserData(user=user),
        )
    except Exception as e:
        logger.exception("HN get user failed")
        return HackerNewsUserResponse(
            success=False, error=f"Hacker News get user failed: {e}"
        )


@tool()
async def hackernews_get_comments(
    story_id: int,
    limit: int = 20,
) -> HackerNewsCommentsResponse:
    """Get top-level comments for a Hacker News story.

    Fetches the direct child comments of a story. Does not recurse into
    nested replies.

    Args:
        story_id: The numeric Hacker News story ID.
        limit: Maximum number of comments to return (default 20, max 50).

    Returns:
        List of top-level comments or an error message.
    """
    try:
        limit = max(1, min(limit, 50))
        logger.info("HN get comments story_id=%d limit=%d", story_id, limit)

        async with httpx.AsyncClient() as client:
            story_resp = await client.get(f"{_HN_API_BASE}/item/{story_id}.json")
            story_resp.raise_for_status()
            story = story_resp.json()

        if story is None:
            return HackerNewsCommentsResponse(
                success=False,
                error=f"Story with ID {story_id} not found.",
            )

        kid_ids = story.get("kids", [])[:limit]
        comments: list[HackerNewsComment] = []

        async with httpx.AsyncClient() as client:
            for kid_id in kid_ids:
                try:
                    resp = await client.get(f"{_HN_API_BASE}/item/{kid_id}.json")
                    resp.raise_for_status()
                    item = resp.json()
                    if item is None or item.get("deleted") or item.get("dead"):
                        continue
                    comments.append(
                        HackerNewsComment(
                            id=item["id"],
                            by=item.get("by"),
                            text=item.get("text"),
                            time=item.get("time", 0),
                            parent=item.get("parent", 0),
                            kids=item.get("kids", []),
                        )
                    )
                except Exception as e:
                    logger.warning("Skipping comment %d: %s", kid_id, e)

        logger.info("HN get comments complete results=%d", len(comments))
        return HackerNewsCommentsResponse(
            success=True,
            data=HackerNewsCommentsData(
                story_id=story_id,
                comments=comments,
            ),
        )
    except Exception as e:
        logger.exception("HN get comments failed")
        return HackerNewsCommentsResponse(
            success=False, error=f"Hacker News get comments failed: {e}"
        )
