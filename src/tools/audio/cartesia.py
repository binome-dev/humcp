"""Cartesia text-to-speech tool."""

from __future__ import annotations

import base64
import logging

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.audio.schemas import (
    CartesiaListVoicesData,
    CartesiaListVoicesResponse,
    CartesiaTTSData,
    CartesiaTTSResponse,
    CartesiaVoice,
)

try:
    import cartesia  # type: ignore
except ImportError as err:
    raise ImportError(
        "cartesia is required for Cartesia tools. Install with: pip install cartesia"
    ) from err

logger = logging.getLogger("humcp.tools.cartesia")


@tool()
async def cartesia_text_to_speech(
    text: str,
    voice_id: str = "78ab82d5-25be-4f7d-82b3-7ad64e5b85b2",
    model_id: str = "sonic-2",
    output_format: str = "mp3",
) -> CartesiaTTSResponse:
    """Convert text to speech using Cartesia API.

    Generates audio from text using a specified voice and model.
    Returns the audio as base64-encoded content.

    Args:
        text: The text to convert to speech.
        voice_id: Cartesia voice ID to use.
        model_id: Model to use for generation (default: sonic-2).
        output_format: Audio container format (default: mp3).

    Returns:
        Success flag with base64-encoded audio data or error message.
    """
    try:
        api_key = await resolve_credential("CARTESIA_API_KEY")
        if not api_key:
            return CartesiaTTSResponse(
                success=False,
                error="Cartesia API not configured. Set CARTESIA_API_KEY.",
            )

        logger.info(
            "Cartesia TTS start voice_id=%s model_id=%s format=%s",
            voice_id,
            model_id,
            output_format,
        )

        client = cartesia.Cartesia(api_key=api_key)

        format_config = {
            "container": output_format,
            "sample_rate": 44100,
            "bit_rate": 128000,
            "encoding": output_format,
        }

        params = {
            "model_id": model_id,
            "transcript": text,
            "voice": {"mode": "id", "id": voice_id},
            "output_format": format_config,
        }

        audio_iterator = client.tts.bytes(**params)
        audio_data = b"".join(chunk for chunk in audio_iterator)

        encoded_audio = base64.b64encode(audio_data).decode("utf-8")

        logger.info("Cartesia TTS complete size=%d bytes", len(audio_data))

        return CartesiaTTSResponse(
            success=True,
            data=CartesiaTTSData(
                audio_base64=encoded_audio,
                format=output_format,
                voice_id=voice_id,
                model_id=model_id,
            ),
        )
    except Exception as e:
        logger.exception("Cartesia TTS failed")
        return CartesiaTTSResponse(
            success=False, error=f"Cartesia TTS failed: {str(e)}"
        )


@tool()
async def cartesia_list_voices() -> CartesiaListVoicesResponse:
    """List all available voices from Cartesia.

    Returns a list of voices with their IDs, names, descriptions,
    and language information.

    Returns:
        Success flag with list of available voices or error message.
    """
    try:
        api_key = await resolve_credential("CARTESIA_API_KEY")
        if not api_key:
            return CartesiaListVoicesResponse(
                success=False,
                error="Cartesia API not configured. Set CARTESIA_API_KEY.",
            )

        logger.info("Cartesia list voices start")

        client = cartesia.Cartesia(api_key=api_key)
        voices_response = client.voices.list()

        voices = [
            CartesiaVoice(
                voice_id=voice.get("id", ""),
                name=voice.get("name", "Unknown"),
                description=voice.get("description"),
                language=voice.get("language"),
                is_public=voice.get("is_public"),
            )
            for voice in voices_response
        ]

        logger.info("Cartesia list voices complete count=%d", len(voices))

        return CartesiaListVoicesResponse(
            success=True,
            data=CartesiaListVoicesData(voices=voices),
        )
    except Exception as e:
        logger.exception("Cartesia list voices failed")
        return CartesiaListVoicesResponse(
            success=False,
            error=f"Cartesia list voices failed: {str(e)}",
        )
