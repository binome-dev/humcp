"""MLX Whisper local audio transcription tool.

Requirements:
    - ffmpeg: Required for audio processing
        macOS: brew install ffmpeg
        Ubuntu: apt-get install ffmpeg
    - mlx-whisper: Install via pip
        pip install mlx-whisper

Optimized for Apple Silicon processors.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.humcp.decorator import tool
from src.tools.audio.schemas import (
    MLXTranscribeData,
    MLXTranscribeResponse,
)

try:
    import mlx_whisper
except ImportError as err:
    raise ImportError(
        "mlx-whisper is required for MLX transcription tools. "
        "Install with: pip install mlx-whisper"
    ) from err

logger = logging.getLogger("humcp.tools.mlx_transcribe")


@tool()
async def mlx_transcribe(
    audio_path: str,
    model: str = "mlx-community/whisper-large-v3-turbo",
    language: str | None = None,
) -> MLXTranscribeResponse:
    """Transcribe audio to text using Apple's MLX Whisper model.

    Uses the MLX framework for fast, local transcription on Apple Silicon.
    Supports various audio formats (mp3, wav, m4a, flac, etc.).
    No API key required -- runs entirely on-device.

    Args:
        audio_path: Path to the audio file to transcribe.
        model: HuggingFace model repo for MLX Whisper
               (default: mlx-community/whisper-large-v3-turbo).
        language: Optional language code (e.g., 'en', 'es', 'fr').
                  Auto-detected if not specified.

    Returns:
        Success flag with transcribed text or error message.
    """
    try:
        resolved_path = Path(audio_path).resolve()
        if not resolved_path.exists():
            return MLXTranscribeResponse(
                success=False,
                error=f"Audio file not found: {audio_path}",
            )

        logger.info(
            "MLX transcribe start path=%s model=%s language=%s",
            resolved_path,
            model,
            language,
        )

        transcription_kwargs: dict = {
            "path_or_hf_repo": model,
        }
        if language is not None:
            transcription_kwargs["language"] = language

        transcription = mlx_whisper.transcribe(
            str(resolved_path), **transcription_kwargs
        )
        text = transcription.get("text", "")
        detected_language = transcription.get("language", language)

        logger.info(
            "MLX transcribe complete chars=%d language=%s",
            len(text),
            detected_language,
        )

        return MLXTranscribeResponse(
            success=True,
            data=MLXTranscribeData(
                text=text,
                audio_path=str(resolved_path),
                model=model,
                language=detected_language,
            ),
        )
    except Exception as e:
        logger.exception("MLX transcribe failed")
        return MLXTranscribeResponse(
            success=False, error=f"MLX transcription failed: {str(e)}"
        )
