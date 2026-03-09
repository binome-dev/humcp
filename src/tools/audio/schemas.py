"""Pydantic output schemas for audio tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# ElevenLabs Schemas
# =============================================================================


class ElevenLabsVoice(BaseModel):
    """A single voice from ElevenLabs."""

    voice_id: str = Field(..., description="Unique voice identifier")
    name: str = Field(..., description="Voice name")
    description: str | None = Field(None, description="Voice description")


class ElevenLabsListVoicesData(BaseModel):
    """Output data for elevenlabs_list_voices tool."""

    voices: list[ElevenLabsVoice] = Field(
        default_factory=list, description="List of available voices"
    )


class ElevenLabsTTSData(BaseModel):
    """Output data for elevenlabs_text_to_speech tool."""

    audio_url: str | None = Field(
        None, description="URL or path of the generated audio file"
    )
    audio_base64: str | None = Field(None, description="Base64-encoded audio content")
    format: str = Field("mp3", description="Audio output format")
    voice_id: str = Field(..., description="Voice ID used for generation")
    model_id: str = Field(..., description="Model ID used for generation")


# =============================================================================
# Cartesia Schemas
# =============================================================================


class CartesiaTTSData(BaseModel):
    """Output data for cartesia_text_to_speech tool."""

    audio_base64: str | None = Field(None, description="Base64-encoded audio content")
    format: str = Field("mp3", description="Audio output format")
    voice_id: str = Field(..., description="Voice ID used for generation")
    model_id: str = Field(..., description="Model ID used for generation")


# =============================================================================
# DesiVocal Schemas
# =============================================================================


class DesiVocalVoice(BaseModel):
    """A single voice from DesiVocal."""

    voice_id: str = Field(..., description="Unique voice identifier")
    name: str = Field(..., description="Voice name")
    gender: str | None = Field(None, description="Voice gender")
    voice_type: str | None = Field(None, description="Voice type")
    language: str | None = Field(None, description="Supported languages")
    preview_url: str | None = Field(None, description="Preview audio URL")


class DesiVocalListVoicesData(BaseModel):
    """Output data for desi_vocal_list_voices tool."""

    voices: list[DesiVocalVoice] = Field(
        default_factory=list, description="List of available voices"
    )


class DesiVocalTTSData(BaseModel):
    """Output data for desi_vocal_tts tool."""

    audio_url: str = Field(..., description="URL of the generated audio file")
    voice_id: str = Field(..., description="Voice ID used for generation")


# =============================================================================
# MLX Transcribe Schemas
# =============================================================================


class MLXTranscribeData(BaseModel):
    """Output data for mlx_transcribe tool."""

    text: str = Field(..., description="Transcribed text from the audio file")
    audio_path: str = Field(
        ..., description="Path of the audio file that was transcribed"
    )
    model: str = Field(..., description="Model used for transcription")
    language: str | None = Field(None, description="Detected or specified language")


# =============================================================================
# Spotify Schemas
# =============================================================================


class SpotifyTrack(BaseModel):
    """A single track from Spotify."""

    track_id: str = Field(..., description="Spotify track ID")
    name: str = Field(..., description="Track name")
    artists: list[str] = Field(default_factory=list, description="List of artist names")
    album: str | None = Field(None, description="Album name")
    uri: str = Field(..., description="Spotify URI")
    preview_url: str | None = Field(None, description="URL for 30-second preview")
    popularity: int | None = Field(None, description="Popularity score (0-100)")
    duration_ms: int | None = Field(None, description="Track duration in milliseconds")


class SpotifySearchData(BaseModel):
    """Output data for spotify_search tool."""

    query: str = Field(..., description="The search query that was executed")
    search_type: str = Field(..., description="Type of search performed")
    tracks: list[SpotifyTrack] = Field(
        default_factory=list, description="List of matching tracks"
    )


class SpotifyTrackData(BaseModel):
    """Output data for spotify_get_track tool."""

    track: SpotifyTrack = Field(..., description="Track details")


class SpotifyPlaylistTrack(BaseModel):
    """A track within a Spotify playlist."""

    track_id: str = Field(..., description="Spotify track ID")
    name: str = Field(..., description="Track name")
    artists: list[str] = Field(default_factory=list, description="List of artist names")
    uri: str = Field(..., description="Spotify URI")


class SpotifyPlaylistData(BaseModel):
    """Output data for spotify_get_playlist tool."""

    playlist_id: str = Field(..., description="Spotify playlist ID")
    name: str = Field(..., description="Playlist name")
    description: str | None = Field(None, description="Playlist description")
    owner: str | None = Field(None, description="Playlist owner display name")
    public: bool | None = Field(None, description="Whether the playlist is public")
    url: str | None = Field(None, description="Spotify URL for the playlist")
    tracks: list[SpotifyPlaylistTrack] = Field(
        default_factory=list, description="List of tracks in the playlist"
    )


# =============================================================================
# Cartesia List Voices Schemas
# =============================================================================


class CartesiaVoice(BaseModel):
    """A single voice from Cartesia."""

    voice_id: str = Field(..., description="Unique voice identifier")
    name: str = Field(..., description="Voice name")
    description: str | None = Field(None, description="Voice description")
    language: str | None = Field(None, description="Voice language")
    is_public: bool | None = Field(
        None, description="Whether the voice is publicly available"
    )


class CartesiaListVoicesData(BaseModel):
    """Output data for cartesia_list_voices tool."""

    voices: list[CartesiaVoice] = Field(
        default_factory=list, description="List of available voices"
    )


# =============================================================================
# Spotify Artist Schemas
# =============================================================================


class SpotifyArtist(BaseModel):
    """An artist from Spotify."""

    artist_id: str = Field(..., description="Spotify artist ID")
    name: str = Field(..., description="Artist name")
    genres: list[str] = Field(default_factory=list, description="List of genres")
    popularity: int | None = Field(None, description="Popularity score (0-100)")
    followers: int | None = Field(None, description="Number of followers")
    uri: str = Field(..., description="Spotify URI")
    image_url: str | None = Field(None, description="Artist image URL")
    external_url: str | None = Field(None, description="Spotify external URL")


class SpotifyArtistData(BaseModel):
    """Output data for spotify_get_artist tool."""

    artist: SpotifyArtist = Field(..., description="Artist details")


# =============================================================================
# Spotify New Releases Schemas
# =============================================================================


class SpotifyAlbum(BaseModel):
    """An album from Spotify."""

    album_id: str = Field(..., description="Spotify album ID")
    name: str = Field(..., description="Album name")
    artists: list[str] = Field(default_factory=list, description="List of artist names")
    release_date: str | None = Field(None, description="Release date")
    total_tracks: int | None = Field(None, description="Total number of tracks")
    album_type: str | None = Field(
        None, description="Album type (album, single, compilation)"
    )
    uri: str = Field(..., description="Spotify URI")
    image_url: str | None = Field(None, description="Album cover image URL")
    external_url: str | None = Field(None, description="Spotify external URL")


class SpotifyNewReleasesData(BaseModel):
    """Output data for spotify_get_new_releases tool."""

    albums: list[SpotifyAlbum] = Field(
        default_factory=list, description="List of new album releases"
    )
    total: int | None = Field(
        None, description="Total number of new releases available"
    )


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class ElevenLabsListVoicesResponse(ToolResponse[ElevenLabsListVoicesData]):
    """Response schema for elevenlabs_list_voices tool."""

    pass


class ElevenLabsTTSResponse(ToolResponse[ElevenLabsTTSData]):
    """Response schema for elevenlabs_text_to_speech tool."""

    pass


class CartesiaTTSResponse(ToolResponse[CartesiaTTSData]):
    """Response schema for cartesia_text_to_speech tool."""

    pass


class DesiVocalListVoicesResponse(ToolResponse[DesiVocalListVoicesData]):
    """Response schema for desi_vocal_list_voices tool."""

    pass


class DesiVocalTTSResponse(ToolResponse[DesiVocalTTSData]):
    """Response schema for desi_vocal_tts tool."""

    pass


class MLXTranscribeResponse(ToolResponse[MLXTranscribeData]):
    """Response schema for mlx_transcribe tool."""

    pass


class SpotifySearchResponse(ToolResponse[SpotifySearchData]):
    """Response schema for spotify_search tool."""

    pass


class SpotifyTrackResponse(ToolResponse[SpotifyTrackData]):
    """Response schema for spotify_get_track tool."""

    pass


class SpotifyPlaylistResponse(ToolResponse[SpotifyPlaylistData]):
    """Response schema for spotify_get_playlist tool."""

    pass


class CartesiaListVoicesResponse(ToolResponse[CartesiaListVoicesData]):
    """Response schema for cartesia_list_voices tool."""

    pass


class SpotifyArtistResponse(ToolResponse[SpotifyArtistData]):
    """Response schema for spotify_get_artist tool."""

    pass


class SpotifyNewReleasesResponse(ToolResponse[SpotifyNewReleasesData]):
    """Response schema for spotify_get_new_releases tool."""

    pass
