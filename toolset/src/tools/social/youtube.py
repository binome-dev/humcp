"""YouTube tools for searching videos, fetching video info, and retrieving captions."""

from __future__ import annotations

import logging
import os

import httpx

from src.humcp.decorator import tool
from src.tools.social.schemas import (
    YouTubeCaptionsData,
    YouTubeCaptionsResponse,
    YouTubeChannelData,
    YouTubeChannelResponse,
    YouTubePlaylistItem,
    YouTubePlaylistItemsData,
    YouTubePlaylistItemsResponse,
    YouTubeSearchData,
    YouTubeSearchResponse,
    YouTubeVideo,
    YouTubeVideoInfoData,
    YouTubeVideoInfoResponse,
)

logger = logging.getLogger("humcp.tools.youtube")

_YT_API_BASE = "https://www.googleapis.com/youtube/v3"


def _get_api_key() -> str | None:
    """Return the YouTube Data API key from environment."""
    return os.getenv("YOUTUBE_API_KEY")


@tool()
async def youtube_search(
    query: str,
    max_results: int = 5,
) -> YouTubeSearchResponse:
    """Search YouTube videos by query.

    Args:
        query: The search query string.
        max_results: Maximum number of video results to return (default 5, max 50).

    Returns:
        Matching videos or an error message.
    """
    try:
        api_key = _get_api_key()
        if not api_key:
            return YouTubeSearchResponse(
                success=False,
                error="YouTube API not configured. Set YOUTUBE_API_KEY environment variable.",
            )

        max_results = max(1, min(max_results, 50))
        logger.info("YouTube search query=%r max_results=%d", query, max_results)

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "key": api_key,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_YT_API_BASE}/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        videos: list[YouTubeVideo] = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId", "")
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = thumbnails.get("high", thumbnails.get("default", {})).get(
                "url"
            )

            videos.append(
                YouTubeVideo(
                    video_id=video_id,
                    title=snippet.get("title", ""),
                    description=snippet.get("description"),
                    channel_id=snippet.get("channelId"),
                    channel_title=snippet.get("channelTitle"),
                    published_at=snippet.get("publishedAt"),
                    thumbnail_url=thumbnail_url,
                )
            )

        logger.info("YouTube search complete results=%d", len(videos))
        return YouTubeSearchResponse(
            success=True,
            data=YouTubeSearchData(
                query=query,
                results=videos,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("YouTube search HTTP error")
        return YouTubeSearchResponse(
            success=False,
            error=f"YouTube API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("YouTube search failed")
        return YouTubeSearchResponse(success=False, error=f"YouTube search failed: {e}")


@tool()
async def youtube_get_video_info(video_id: str) -> YouTubeVideoInfoResponse:
    """Get detailed information about a YouTube video.

    Args:
        video_id: The YouTube video ID (e.g. "dQw4w9WgXcQ").

    Returns:
        Video details including statistics, or an error message.
    """
    try:
        api_key = _get_api_key()
        if not api_key:
            return YouTubeVideoInfoResponse(
                success=False,
                error="YouTube API not configured. Set YOUTUBE_API_KEY environment variable.",
            )

        logger.info("YouTube get video info id=%s", video_id)

        params = {
            "part": "snippet,contentDetails,statistics",
            "id": video_id,
            "key": api_key,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_YT_API_BASE}/videos",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        items = data.get("items", [])
        if not items:
            return YouTubeVideoInfoResponse(
                success=False,
                error=f"Video with ID '{video_id}' not found.",
            )

        item = items[0]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        content_details = item.get("contentDetails", {})
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = thumbnails.get("high", thumbnails.get("default", {})).get("url")

        def _safe_int(value: str | None) -> int | None:
            if value is None:
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None

        return YouTubeVideoInfoResponse(
            success=True,
            data=YouTubeVideoInfoData(
                video_id=video_id,
                title=snippet.get("title", ""),
                description=snippet.get("description"),
                channel_title=snippet.get("channelTitle"),
                published_at=snippet.get("publishedAt"),
                view_count=_safe_int(stats.get("viewCount")),
                like_count=_safe_int(stats.get("likeCount")),
                comment_count=_safe_int(stats.get("commentCount")),
                duration=content_details.get("duration"),
                thumbnail_url=thumbnail_url,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("YouTube get video info HTTP error")
        return YouTubeVideoInfoResponse(
            success=False,
            error=f"YouTube API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("YouTube get video info failed")
        return YouTubeVideoInfoResponse(
            success=False, error=f"YouTube get video info failed: {e}"
        )


@tool()
async def youtube_get_captions(video_id: str) -> YouTubeCaptionsResponse:
    """Get the captions (transcript) of a YouTube video.

    Uses the youtube-transcript-api library to fetch available captions.

    Args:
        video_id: The YouTube video ID (e.g. "dQw4w9WgXcQ").

    Returns:
        Concatenated caption text or an error message.
    """
    try:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
        except ImportError:
            return YouTubeCaptionsResponse(
                success=False,
                error="youtube-transcript-api is required for captions. Install with: pip install youtube-transcript-api",
            )

        logger.info("YouTube get captions id=%s", video_id)

        captions = YouTubeTranscriptApi().fetch(video_id)
        if not captions:
            return YouTubeCaptionsResponse(
                success=False,
                error=f"No captions found for video '{video_id}'.",
            )

        caption_text = " ".join(line.text for line in captions)

        logger.info("YouTube captions complete length=%d", len(caption_text))
        return YouTubeCaptionsResponse(
            success=True,
            data=YouTubeCaptionsData(
                video_id=video_id,
                captions=caption_text,
            ),
        )
    except Exception as e:
        logger.exception("YouTube get captions failed")
        return YouTubeCaptionsResponse(
            success=False, error=f"YouTube get captions failed: {e}"
        )


@tool()
async def youtube_get_channel(
    channel_id: str | None = None,
    username: str | None = None,
) -> YouTubeChannelResponse:
    """Get information about a YouTube channel.

    Provide either a channel_id or a username. Returns channel metadata
    including subscriber count, video count, and the uploads playlist ID.

    Args:
        channel_id: The YouTube channel ID (e.g. "UC_x5XG1OV2P6uZZ5FSM9Ttw"). Provide this or username.
        username: The YouTube channel username/handle (e.g. "GoogleDevelopers"). Provide this or channel_id.

    Returns:
        Channel details including statistics or an error message.
    """
    try:
        api_key = _get_api_key()
        if not api_key:
            return YouTubeChannelResponse(
                success=False,
                error="YouTube API not configured. Set YOUTUBE_API_KEY environment variable.",
            )

        if not channel_id and not username:
            return YouTubeChannelResponse(
                success=False,
                error="Provide either channel_id or username.",
            )

        logger.info("YouTube get channel id=%s username=%s", channel_id, username)

        params: dict = {
            "part": "snippet,statistics,contentDetails",
            "key": api_key,
        }
        if channel_id:
            params["id"] = channel_id
        else:
            params["forHandle"] = username

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_YT_API_BASE}/channels",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        items = data.get("items", [])
        if not items:
            return YouTubeChannelResponse(
                success=False,
                error=f"Channel not found for {'id=' + channel_id if channel_id else 'username=' + str(username)}.",
            )

        item = items[0]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        content_details = item.get("contentDetails", {})
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = thumbnails.get("high", thumbnails.get("default", {})).get("url")

        def _safe_int(value: str | None) -> int | None:
            if value is None:
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None

        uploads_playlist = content_details.get("relatedPlaylists", {}).get("uploads")

        return YouTubeChannelResponse(
            success=True,
            data=YouTubeChannelData(
                channel_id=item["id"],
                title=snippet.get("title", ""),
                description=snippet.get("description"),
                custom_url=snippet.get("customUrl"),
                published_at=snippet.get("publishedAt"),
                thumbnail_url=thumbnail_url,
                subscriber_count=_safe_int(stats.get("subscriberCount")),
                video_count=_safe_int(stats.get("videoCount")),
                view_count=_safe_int(stats.get("viewCount")),
                uploads_playlist_id=uploads_playlist,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("YouTube get channel HTTP error")
        return YouTubeChannelResponse(
            success=False,
            error=f"YouTube API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("YouTube get channel failed")
        return YouTubeChannelResponse(
            success=False, error=f"YouTube get channel failed: {e}"
        )


@tool()
async def youtube_get_playlist_items(
    playlist_id: str,
    max_results: int = 10,
) -> YouTubePlaylistItemsResponse:
    """Get videos from a YouTube playlist.

    Retrieves items from any playlist, including a channel's uploads playlist
    (use youtube_get_channel to get the uploads_playlist_id first).

    Args:
        playlist_id: The YouTube playlist ID (e.g. "PLIivdWyY5sqJxnwJhe3ETaK6uFCfkheUk").
        max_results: Maximum number of items to return (default 10, max 50).

    Returns:
        List of playlist items or an error message.
    """
    try:
        api_key = _get_api_key()
        if not api_key:
            return YouTubePlaylistItemsResponse(
                success=False,
                error="YouTube API not configured. Set YOUTUBE_API_KEY environment variable.",
            )

        max_results = max(1, min(max_results, 50))
        logger.info(
            "YouTube get playlist items id=%s max_results=%d", playlist_id, max_results
        )

        params = {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": max_results,
            "key": api_key,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_YT_API_BASE}/playlistItems",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        page_info = data.get("pageInfo", {})
        total_results = page_info.get("totalResults")

        items: list[YouTubePlaylistItem] = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            content_details = item.get("contentDetails", {})
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = thumbnails.get("high", thumbnails.get("default", {})).get(
                "url"
            )

            video_id = content_details.get(
                "videoId", snippet.get("resourceId", {}).get("videoId", "")
            )

            items.append(
                YouTubePlaylistItem(
                    video_id=video_id,
                    title=snippet.get("title", ""),
                    description=snippet.get("description"),
                    channel_id=snippet.get("videoOwnerChannelId"),
                    channel_title=snippet.get("videoOwnerChannelTitle"),
                    published_at=snippet.get("publishedAt"),
                    position=snippet.get("position", 0),
                    thumbnail_url=thumbnail_url,
                )
            )

        logger.info("YouTube get playlist items complete results=%d", len(items))
        return YouTubePlaylistItemsResponse(
            success=True,
            data=YouTubePlaylistItemsData(
                playlist_id=playlist_id,
                items=items,
                total_results=total_results,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("YouTube get playlist items HTTP error")
        return YouTubePlaylistItemsResponse(
            success=False,
            error=f"YouTube API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("YouTube get playlist items failed")
        return YouTubePlaylistItemsResponse(
            success=False, error=f"YouTube get playlist items failed: {e}"
        )
