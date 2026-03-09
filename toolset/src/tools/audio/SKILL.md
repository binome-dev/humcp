---
name: audio-tools
description: Text-to-speech synthesis, audio transcription, and music search. Use when the user needs to generate speech audio, transcribe audio files, or search for music on Spotify.
---

# Audio Tools

Tools for text-to-speech, transcription, and music search.

## ElevenLabs (Text-to-Speech)

### Generate speech

```python
result = await elevenlabs_text_to_speech(
    text="Hello, welcome to the demo.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_64"
)
```

### List voices

```python
result = await elevenlabs_list_voices()
```

**Env:** `ELEVEN_LABS_API_KEY`

## Cartesia (Text-to-Speech)

### Generate speech

```python
result = await cartesia_text_to_speech(
    text="Hello from Cartesia.",
    voice_id="78ab82d5-25be-4f7d-82b3-7ad64e5b85b2",
    model_id="sonic-2",
    output_format="mp3"
)
```

**Env:** `CARTESIA_API_KEY`

## DesiVocal (Text-to-Speech)

### Generate speech

```python
result = await desi_vocal_tts(
    text="Namaste, yeh ek demo hai.",
    voice_id="f27d74e5-ea71-4697-be3e-f04bbd80c1a8"
)
```

### List voices

```python
result = await desi_vocal_list_voices()
```

**Env:** `DESI_VOCAL_API_KEY`

## MLX Transcribe (Speech-to-Text)

### Transcribe audio

```python
result = await mlx_transcribe(
    audio_path="/path/to/audio.mp3",
    model="mlx-community/whisper-large-v3-turbo",
    language="en"
)
```

No API key required. Runs locally on Apple Silicon via MLX Whisper.

**Requirements:** `pip install mlx-whisper`, `brew install ffmpeg`

## Spotify (Music Search)

### Search tracks

```python
result = await spotify_search(
    query="Bohemian Rhapsody",
    search_type="track",
    limit=10
)
```

### Get track details

```python
result = await spotify_get_track(track_id="4u7EnebtmKWzUH433cf5Qv")
```

### Get playlist

```python
result = await spotify_get_playlist(playlist_id="37i9dQZF1DXcBWIGoYBM5M")
```

**Env:** `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`

## Response Format

All tools return:
```json
{
  "success": true,
  "data": { ... }
}
```

On error:
```json
{
  "success": false,
  "error": "Error description"
}
```

## When to Use

- Generating speech audio from text (ElevenLabs, Cartesia, DesiVocal)
- Transcribing audio files to text (MLX Transcribe)
- Searching for songs, albums, or playlists (Spotify)
- Building voice-enabled workflows
- Creating audio content pipelines
