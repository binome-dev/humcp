"""Spotify Web API tools for searching tracks, getting track details, and playlists."""

from __future__ import annotations

import logging
import os

import httpx

from src.humcp.decorator import tool
from src.tools.audio.schemas import (
    SpotifyAlbum,
    SpotifyArtist,
    SpotifyArtistData,
    SpotifyArtistResponse,
    SpotifyNewReleasesData,
    SpotifyNewReleasesResponse,
    SpotifyPlaylistData,
    SpotifyPlaylistResponse,
    SpotifyPlaylistTrack,
    SpotifySearchData,
    SpotifySearchResponse,
    SpotifyTrack,
    SpotifyTrackData,
    SpotifyTrackResponse,
)

logger = logging.getLogger("humcp.tools.spotify")

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"


async def _get_spotify_token() -> str | None:
    """Obtain a Spotify access token via Client Credentials flow."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            SPOTIFY_TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def _spotify_request(
    endpoint: str,
    token: str,
    params: dict | None = None,
) -> dict:
    """Make an authenticated GET request to the Spotify Web API."""
    url = f"{SPOTIFY_API_BASE}/{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


@tool()
async def spotify_search(
    query: str,
    search_type: str = "track",
    limit: int = 10,
    market: str = "US",
) -> SpotifySearchResponse:
    """Search for tracks on Spotify.

    Find songs by name, artist, album, or any combination of keywords.

    Args:
        query: Search query (e.g., 'Bohemian Rhapsody', 'Coldplay Paradise').
        search_type: Type of search -- 'track' (default).
        limit: Maximum number of results to return (default: 10, max: 50).
        market: Country code for market (default: 'US').

    Returns:
        Success flag with list of matching tracks or error message.
    """
    try:
        token = await _get_spotify_token()
        if not token:
            return SpotifySearchResponse(
                success=False,
                error="Spotify API not configured. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.",
            )

        logger.info(
            "Spotify search start query=%s type=%s limit=%d",
            query,
            search_type,
            limit,
        )

        params = {
            "q": query,
            "type": search_type,
            "limit": min(limit, 50),
            "market": market,
        }

        result = await _spotify_request("search", token, params=params)

        tracks_data = result.get("tracks", {}).get("items", [])
        tracks = [
            SpotifyTrack(
                track_id=track["id"],
                name=track["name"],
                artists=[artist["name"] for artist in track["artists"]],
                album=track["album"]["name"],
                uri=track["uri"],
                preview_url=track.get("preview_url"),
                popularity=track.get("popularity"),
                duration_ms=track.get("duration_ms"),
            )
            for track in tracks_data
        ]

        logger.info("Spotify search complete results=%d", len(tracks))

        return SpotifySearchResponse(
            success=True,
            data=SpotifySearchData(
                query=query,
                search_type=search_type,
                tracks=tracks,
            ),
        )
    except Exception as e:
        logger.exception("Spotify search failed")
        return SpotifySearchResponse(
            success=False, error=f"Spotify search failed: {str(e)}"
        )


@tool()
async def spotify_get_track(
    track_id: str,
    market: str = "US",
) -> SpotifyTrackResponse:
    """Get details of a specific Spotify track by its ID.

    Args:
        track_id: The Spotify track ID.
        market: Country code for market (default: 'US').

    Returns:
        Success flag with track details or error message.
    """
    try:
        token = await _get_spotify_token()
        if not token:
            return SpotifyTrackResponse(
                success=False,
                error="Spotify API not configured. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.",
            )

        logger.info("Spotify get track start track_id=%s", track_id)

        result = await _spotify_request(
            f"tracks/{track_id}", token, params={"market": market}
        )

        track = SpotifyTrack(
            track_id=result["id"],
            name=result["name"],
            artists=[artist["name"] for artist in result["artists"]],
            album=result["album"]["name"],
            uri=result["uri"],
            preview_url=result.get("preview_url"),
            popularity=result.get("popularity"),
            duration_ms=result.get("duration_ms"),
        )

        logger.info("Spotify get track complete name=%s", track.name)

        return SpotifyTrackResponse(
            success=True,
            data=SpotifyTrackData(track=track),
        )
    except Exception as e:
        logger.exception("Spotify get track failed")
        return SpotifyTrackResponse(
            success=False, error=f"Spotify get track failed: {str(e)}"
        )


@tool()
async def spotify_get_playlist(
    playlist_id: str,
    market: str = "US",
) -> SpotifyPlaylistResponse:
    """Get details and tracks of a Spotify playlist by its ID.

    Args:
        playlist_id: The Spotify playlist ID.
        market: Country code for market (default: 'US').

    Returns:
        Success flag with playlist details and tracks or error message.
    """
    try:
        token = await _get_spotify_token()
        if not token:
            return SpotifyPlaylistResponse(
                success=False,
                error="Spotify API not configured. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.",
            )

        logger.info("Spotify get playlist start playlist_id=%s", playlist_id)

        params = {
            "fields": "id,name,description,public,owner(display_name),external_urls,tracks.items(track(id,name,artists(name),uri))",
            "market": market,
        }

        result = await _spotify_request(
            f"playlists/{playlist_id}", token, params=params
        )

        tracks = [
            SpotifyPlaylistTrack(
                track_id=item["track"]["id"],
                name=item["track"]["name"],
                artists=[a["name"] for a in item["track"]["artists"]],
                uri=item["track"]["uri"],
            )
            for item in result.get("tracks", {}).get("items", [])
            if item.get("track")
        ]

        logger.info(
            "Spotify get playlist complete name=%s tracks=%d",
            result.get("name"),
            len(tracks),
        )

        return SpotifyPlaylistResponse(
            success=True,
            data=SpotifyPlaylistData(
                playlist_id=result["id"],
                name=result["name"],
                description=result.get("description"),
                owner=result.get("owner", {}).get("display_name"),
                public=result.get("public"),
                url=result.get("external_urls", {}).get("spotify"),
                tracks=tracks,
            ),
        )
    except Exception as e:
        logger.exception("Spotify get playlist failed")
        return SpotifyPlaylistResponse(
            success=False, error=f"Spotify get playlist failed: {str(e)}"
        )


@tool()
async def spotify_get_artist(
    artist_id: str,
) -> SpotifyArtistResponse:
    """Get details of a Spotify artist by their ID.

    Retrieves artist information including name, genres, popularity,
    follower count, and image.

    Args:
        artist_id: The Spotify artist ID.

    Returns:
        Success flag with artist details or error message.
    """
    try:
        token = await _get_spotify_token()
        if not token:
            return SpotifyArtistResponse(
                success=False,
                error="Spotify API not configured. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.",
            )

        logger.info("Spotify get artist start artist_id=%s", artist_id)

        result = await _spotify_request(f"artists/{artist_id}", token)

        images = result.get("images", [])
        image_url = images[0]["url"] if images else None

        artist = SpotifyArtist(
            artist_id=result["id"],
            name=result["name"],
            genres=result.get("genres", []),
            popularity=result.get("popularity"),
            followers=result.get("followers", {}).get("total"),
            uri=result["uri"],
            image_url=image_url,
            external_url=result.get("external_urls", {}).get("spotify"),
        )

        logger.info("Spotify get artist complete name=%s", artist.name)

        return SpotifyArtistResponse(
            success=True,
            data=SpotifyArtistData(artist=artist),
        )
    except Exception as e:
        logger.exception("Spotify get artist failed")
        return SpotifyArtistResponse(
            success=False, error=f"Spotify get artist failed: {str(e)}"
        )


@tool()
async def spotify_get_new_releases(
    country: str = "US",
    limit: int = 20,
) -> SpotifyNewReleasesResponse:
    """Get a list of new album releases on Spotify.

    Retrieves the latest album releases available in a given market.

    Args:
        country: ISO 3166-1 alpha-2 country code (default: 'US').
        limit: Maximum number of releases to return (default: 20, max: 50).

    Returns:
        Success flag with list of new album releases or error message.
    """
    try:
        token = await _get_spotify_token()
        if not token:
            return SpotifyNewReleasesResponse(
                success=False,
                error="Spotify API not configured. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.",
            )

        logger.info(
            "Spotify get new releases start country=%s limit=%d",
            country,
            limit,
        )

        params = {
            "country": country,
            "limit": min(limit, 50),
        }

        result = await _spotify_request("browse/new-releases", token, params=params)

        albums_data = result.get("albums", {})
        items = albums_data.get("items", [])

        albums = [
            SpotifyAlbum(
                album_id=album["id"],
                name=album["name"],
                artists=[a["name"] for a in album.get("artists", [])],
                release_date=album.get("release_date"),
                total_tracks=album.get("total_tracks"),
                album_type=album.get("album_type"),
                uri=album["uri"],
                image_url=(album["images"][0]["url"] if album.get("images") else None),
                external_url=album.get("external_urls", {}).get("spotify"),
            )
            for album in items
        ]

        logger.info("Spotify get new releases complete count=%d", len(albums))

        return SpotifyNewReleasesResponse(
            success=True,
            data=SpotifyNewReleasesData(
                albums=albums,
                total=albums_data.get("total"),
            ),
        )
    except Exception as e:
        logger.exception("Spotify get new releases failed")
        return SpotifyNewReleasesResponse(
            success=False,
            error=f"Spotify get new releases failed: {str(e)}",
        )
