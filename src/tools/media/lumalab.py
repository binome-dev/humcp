"""Luma AI video generation tool."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.media.schemas import (
    LumaLabVideoData,
    LumaLabVideoResponse,
)

logger = logging.getLogger("humcp.tools.lumalab")

POLL_INTERVAL_SECONDS = 3
MAX_WAIT_SECONDS = 300


@tool()
async def lumalab_generate_video(
    prompt: str,
    keyframes: dict[str, dict[str, str]] | None = None,
    loop: bool = False,
    aspect_ratio: str = "16:9",
) -> LumaLabVideoResponse:
    """Generate a video using Luma AI from a text prompt.

    Args:
        prompt: A text description of the desired video content.
        keyframes: Optional keyframe images for guided generation.
            Format: {"frame0": {"type": "image", "url": "https://..."}}
        loop: Whether the video should loop seamlessly. Default: False.
        aspect_ratio: Aspect ratio of the output video. Options: "1:1", "16:9",
            "9:16", "4:3", "3:4", "21:9", "9:21". Default: "16:9".

    Returns:
        Video URL and generation status.
    """
    try:
        api_key = await resolve_credential("LUMAAI_API_KEY")
        if not api_key:
            return LumaLabVideoResponse(
                success=False,
                error="Luma AI API not configured. Set LUMAAI_API_KEY environment variable.",
            )

        if not prompt.strip():
            return LumaLabVideoResponse(
                success=False, error="Prompt must not be empty."
            )

        valid_ratios = {"1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21"}
        if aspect_ratio not in valid_ratios:
            return LumaLabVideoResponse(
                success=False,
                error=f"Invalid aspect_ratio '{aspect_ratio}'. Choose from: {', '.join(valid_ratios)}",
            )

        try:
            from lumaai import LumaAI
        except ImportError:
            return LumaLabVideoResponse(
                success=False,
                error="lumaai package is required. Install with: pip install lumaai",
            )

        logger.info(
            "LumaLab generating video prompt_length=%d aspect_ratio=%s",
            len(prompt),
            aspect_ratio,
        )

        client = LumaAI(auth_token=api_key)

        generation_params: dict[str, Any] = {
            "prompt": prompt,
            "loop": loop,
            "aspect_ratio": aspect_ratio,
        }

        if keyframes is not None:
            generation_params["keyframes"] = keyframes

        generation = client.generations.create(**generation_params)

        if not generation or not generation.id:
            return LumaLabVideoResponse(
                success=False, error="Failed to start video generation."
            )

        generation_id = generation.id

        seconds_waited = 0
        while seconds_waited < MAX_WAIT_SECONDS:
            generation = client.generations.get(generation_id)

            if generation.state == "completed" and generation.assets:
                video_url = generation.assets.video
                if video_url:
                    logger.info("LumaLab video generation completed url=%s", video_url)
                    return LumaLabVideoResponse(
                        success=True,
                        data=LumaLabVideoData(
                            prompt=prompt,
                            video_url=video_url,
                            state="completed",
                            generation_id=generation_id,
                        ),
                    )

            if generation.state == "failed":
                failure_reason = getattr(generation, "failure_reason", "Unknown error")
                logger.error(
                    "LumaLab video generation failed reason=%s", failure_reason
                )
                return LumaLabVideoResponse(
                    success=False,
                    error=f"Video generation failed: {failure_reason}",
                )

            logger.info(
                "LumaLab generation in progress state=%s waited=%ds",
                generation.state,
                seconds_waited,
            )
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            seconds_waited += POLL_INTERVAL_SECONDS

        return LumaLabVideoResponse(
            success=False,
            error=f"Video generation timed out after {MAX_WAIT_SECONDS} seconds.",
        )
    except Exception as e:
        logger.exception("LumaLab video generation failed")
        return LumaLabVideoResponse(
            success=False, error=f"LumaLab video generation failed: {str(e)}"
        )
