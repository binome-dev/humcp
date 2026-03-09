"""ElevenLabs text-to-speech and voice listing tools."""

from __future__ import annotations

import base64
import logging
import os
from io import BytesIO

from src.humcp.decorator import tool
from src.tools.audio.schemas import (
    ElevenLabsListVoicesData,
    ElevenLabsListVoicesResponse,
    ElevenLabsTTSData,
    ElevenLabsTTSResponse,
    ElevenLabsVoice,
)

try:
    from elevenlabs import ElevenLabs
except ImportError as err:
    raise ImportError(
        "elevenlabs is required for ElevenLabs tools. "
        "Install with: pip install elevenlabs"
    ) from err

logger = logging.getLogger("humcp.tools.eleven_labs")


@tool()
async def elevenlabs_text_to_speech(
    text: str,
    voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
    model_id: str = "eleven_multilingual_v2",
    output_format: str = "mp3_44100_64",
) -> ElevenLabsTTSResponse:
    """Convert text to speech using ElevenLabs API.

    Generates audio from text using a specified voice and model.
    Returns the audio as base64-encoded content.

    Args:
        text: The text to convert to speech.
        voice_id: ElevenLabs voice ID to use (default: George).
        model_id: Model to use for generation (default: eleven_multilingual_v2).
        output_format: Audio output format (e.g., mp3_44100_64, mp3_44100_128).

    Returns:
        Success flag with base64-encoded audio data or error message.
    """
    try:
        api_key = os.getenv("ELEVEN_LABS_API_KEY")
        if not api_key:
            return ElevenLabsTTSResponse(
                success=False,
                error="ElevenLabs API not configured. Set ELEVEN_LABS_API_KEY.",
            )

        logger.info(
            "ElevenLabs TTS start voice_id=%s model_id=%s format=%s",
            voice_id,
            model_id,
            output_format,
        )

        client = ElevenLabs(api_key=api_key)
        audio_generator = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format=output_format,
        )

        audio_bytes = BytesIO()
        for chunk in audio_generator:
            audio_bytes.write(chunk)
        audio_bytes.seek(0)
        audio_data = audio_bytes.read()

        encoded_audio = base64.b64encode(audio_data).decode("utf-8")

        logger.info("ElevenLabs TTS complete size=%d bytes", len(audio_data))

        return ElevenLabsTTSResponse(
            success=True,
            data=ElevenLabsTTSData(
                audio_base64=encoded_audio,
                format=output_format.split("_")[0],
                voice_id=voice_id,
                model_id=model_id,
            ),
        )
    except Exception as e:
        logger.exception("ElevenLabs TTS failed")
        return ElevenLabsTTSResponse(
            success=False, error=f"ElevenLabs TTS failed: {str(e)}"
        )


@tool()
async def elevenlabs_list_voices() -> ElevenLabsListVoicesResponse:
    """List all available voices from ElevenLabs.

    Returns a list of voices with their IDs, names, and descriptions.

    Returns:
        Success flag with list of available voices or error message.
    """
    try:
        api_key = os.getenv("ELEVEN_LABS_API_KEY")
        if not api_key:
            return ElevenLabsListVoicesResponse(
                success=False,
                error="ElevenLabs API not configured. Set ELEVEN_LABS_API_KEY.",
            )

        logger.info("ElevenLabs list voices start")

        client = ElevenLabs(api_key=api_key)
        voices_response = client.voices.get_all()

        voices = [
            ElevenLabsVoice(
                voice_id=voice.voice_id,
                name=voice.name,
                description=voice.description,
            )
            for voice in voices_response.voices
        ]

        logger.info("ElevenLabs list voices complete count=%d", len(voices))

        return ElevenLabsListVoicesResponse(
            success=True,
            data=ElevenLabsListVoicesData(voices=voices),
        )
    except Exception as e:
        logger.exception("ElevenLabs list voices failed")
        return ElevenLabsListVoicesResponse(
            success=False, error=f"ElevenLabs list voices failed: {str(e)}"
        )
