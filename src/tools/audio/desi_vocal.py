"""DesiVocal text-to-speech and voice listing tools."""

from __future__ import annotations

import logging

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.audio.schemas import (
    DesiVocalListVoicesData,
    DesiVocalListVoicesResponse,
    DesiVocalTTSData,
    DesiVocalTTSResponse,
    DesiVocalVoice,
)

logger = logging.getLogger("humcp.tools.desi_vocal")

DESI_VOCAL_BASE_URL = "https://prod-api2.desivocal.com/dv/api/v0/tts_api"


@tool()
async def desi_vocal_tts(
    text: str,
    voice_id: str = "f27d74e5-ea71-4697-be3e-f04bbd80c1a8",
) -> DesiVocalTTSResponse:
    """Generate speech audio from text using DesiVocal API.

    Converts text to speech with support for multiple Indian languages and voices.
    Returns the URL of the generated audio file.

    Args:
        text: The text to convert to speech.
        voice_id: DesiVocal voice ID to use for generation.

    Returns:
        Success flag with audio URL or error message.
    """
    try:
        api_key = await resolve_credential("DESI_VOCAL_API_KEY")
        if not api_key:
            return DesiVocalTTSResponse(
                success=False,
                error="DesiVocal API not configured. Set DESI_VOCAL_API_KEY.",
            )

        logger.info("DesiVocal TTS start voice_id=%s", voice_id)

        url = f"{DESI_VOCAL_BASE_URL}/generate"
        payload = {
            "text": text,
            "voice_id": voice_id,
        }
        headers = {
            "X_API_KEY": api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        response_json = response.json()
        audio_url = response_json["s3_path"]

        logger.info("DesiVocal TTS complete audio_url=%s", audio_url)

        return DesiVocalTTSResponse(
            success=True,
            data=DesiVocalTTSData(
                audio_url=audio_url,
                voice_id=voice_id,
            ),
        )
    except Exception as e:
        logger.exception("DesiVocal TTS failed")
        return DesiVocalTTSResponse(
            success=False, error=f"DesiVocal TTS failed: {str(e)}"
        )


@tool()
async def desi_vocal_list_voices() -> DesiVocalListVoicesResponse:
    """List all available voices from DesiVocal.

    Returns a list of voices with their IDs, names, genders, types,
    supported languages, and preview URLs.

    Returns:
        Success flag with list of available voices or error message.
    """
    try:
        logger.info("DesiVocal list voices start")

        url = f"{DESI_VOCAL_BASE_URL}/voices"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()

        voices_data = response.json()

        voices = [
            DesiVocalVoice(
                voice_id=voice_id,
                name=voice_info["name"],
                gender=voice_info.get("audio_gender"),
                voice_type=voice_info.get("voice_type"),
                language=", ".join(voice_info.get("languages", [])),
                preview_url=next(
                    iter(voice_info.get("preview_path", {}).values()), None
                ),
            )
            for voice_id, voice_info in voices_data.items()
        ]

        logger.info("DesiVocal list voices complete count=%d", len(voices))

        return DesiVocalListVoicesResponse(
            success=True,
            data=DesiVocalListVoicesData(voices=voices),
        )
    except Exception as e:
        logger.exception("DesiVocal list voices failed")
        return DesiVocalListVoicesResponse(
            success=False, error=f"DesiVocal list voices failed: {str(e)}"
        )
