"""ModelsLab image generation tool."""

from __future__ import annotations

import logging
import os

import httpx

from src.humcp.decorator import tool
from src.tools.media.schemas import (
    ModelsLabGenerateData,
    ModelsLabGenerateResponse,
)

logger = logging.getLogger("humcp.tools.models_labs")

MODELS_LAB_TEXT2IMG_URL = "https://modelslab.com/api/v6/images/text2img"


@tool()
async def models_labs_generate_image(
    prompt: str,
    model_id: str = "flux",
    width: int = 512,
    height: int = 512,
    num_inference_steps: int = 30,
) -> ModelsLabGenerateResponse:
    """Generate an image using ModelsLab API from a text prompt.

    Args:
        prompt: A text description of the desired image.
        model_id: The ModelsLab model to use. Default: "flux".
        width: Output image width in pixels. Default: 512.
        height: Output image height in pixels. Default: 512.
        num_inference_steps: Number of inference steps. Higher values produce
            better quality but take longer. Default: 30.

    Returns:
        Generated image URLs and status.
    """
    try:
        api_key = os.getenv("MODELS_LAB_API_KEY")
        if not api_key:
            return ModelsLabGenerateResponse(
                success=False,
                error="ModelsLab API not configured. Set MODELS_LAB_API_KEY environment variable.",
            )

        if not prompt.strip():
            return ModelsLabGenerateResponse(
                success=False, error="Prompt must not be empty."
            )

        if width < 64 or height < 64:
            return ModelsLabGenerateResponse(
                success=False, error="Width and height must be at least 64 pixels."
            )

        payload = {
            "key": api_key,
            "prompt": prompt,
            "model_id": model_id,
            "width": width,
            "height": height,
            "samples": 1,
            "num_inference_steps": num_inference_steps,
            "safety_checker": "no",
            "webhook": None,
            "track_id": None,
        }

        logger.info(
            "ModelsLab generating image model=%s size=%dx%d",
            model_id,
            width,
            height,
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                MODELS_LAB_TEXT2IMG_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

        result = response.json()

        status = result.get("status", "unknown")
        if status == "error":
            error_msg = result.get("message", "Unknown error from ModelsLab")
            logger.error("ModelsLab error: %s", error_msg)
            return ModelsLabGenerateResponse(
                success=False, error=f"ModelsLab error: {error_msg}"
            )

        output_urls = result.get("output") or result.get("future_links", [])
        eta = result.get("eta")

        logger.info(
            "ModelsLab generation status=%s urls=%d eta=%s",
            status,
            len(output_urls),
            eta,
        )

        return ModelsLabGenerateResponse(
            success=True,
            data=ModelsLabGenerateData(
                prompt=prompt,
                status=status,
                output_urls=output_urls,
                eta=int(eta) if eta is not None else None,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("ModelsLab HTTP error status=%d", e.response.status_code)
        return ModelsLabGenerateResponse(
            success=False, error=f"ModelsLab API error: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("ModelsLab generation failed")
        return ModelsLabGenerateResponse(
            success=False, error=f"ModelsLab generation failed: {str(e)}"
        )
