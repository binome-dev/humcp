"""DALL-E image generation tool using OpenAI API."""

from __future__ import annotations

import logging
import os
from typing import Literal

from src.humcp.decorator import tool
from src.tools.media.schemas import (
    DalleGeneratedImage,
    DalleGenerateImageData,
    DalleGenerateImageResponse,
)

logger = logging.getLogger("humcp.tools.dalle")


@tool()
async def dalle_generate_image(
    prompt: str,
    size: Literal[
        "256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"
    ] = "1024x1024",
    quality: Literal["standard", "hd"] = "standard",
    style: Literal["vivid", "natural"] = "vivid",
    model: str = "dall-e-3",
) -> DalleGenerateImageResponse:
    """Generate an image using OpenAI DALL-E from a text prompt.

    Args:
        prompt: A text description of the desired image.
        size: Image dimensions. Options: "256x256", "512x512", "1024x1024",
            "1792x1024", "1024x1792". Default: "1024x1024".
        quality: Image quality. "standard" or "hd". Default: "standard".
        style: Image style. "vivid" for hyper-real and dramatic images, or
            "natural" for more natural, less hyper-real images. Default: "vivid".
        model: DALL-E model to use. "dall-e-3" or "dall-e-2". Default: "dall-e-3".

    Returns:
        Generated image URL and revised prompt.
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return DalleGenerateImageResponse(
                success=False,
                error="OpenAI API not configured. Set OPENAI_API_KEY environment variable.",
            )

        if not prompt.strip():
            return DalleGenerateImageResponse(
                success=False, error="Prompt must not be empty."
            )

        valid_models = {"dall-e-3", "dall-e-2"}
        if model not in valid_models:
            return DalleGenerateImageResponse(
                success=False,
                error=f"Invalid model '{model}'. Choose from: {', '.join(valid_models)}",
            )

        valid_sizes = {"256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"}
        if size not in valid_sizes:
            return DalleGenerateImageResponse(
                success=False,
                error=f"Invalid size '{size}'. Choose from: {', '.join(valid_sizes)}",
            )

        try:
            from openai import OpenAI
        except ImportError:
            return DalleGenerateImageResponse(
                success=False,
                error="openai package is required. Install with: pip install openai",
            )

        logger.info(
            "DALL-E generating image model=%s size=%s quality=%s style=%s",
            model,
            size,
            quality,
            style,
        )

        client = OpenAI(api_key=api_key)
        response = client.images.generate(
            prompt=prompt,
            model=model,
            n=1,
            quality=quality,
            size=size,
            style=style,
        )

        images = []
        if response.data:
            for img in response.data:
                if img.url:
                    images.append(
                        DalleGeneratedImage(
                            url=img.url,
                            revised_prompt=img.revised_prompt,
                        )
                    )

        if not images:
            return DalleGenerateImageResponse(
                success=False, error="No images were generated."
            )

        logger.info("DALL-E generation complete images=%d", len(images))

        return DalleGenerateImageResponse(
            success=True,
            data=DalleGenerateImageData(
                prompt=prompt,
                images=images,
            ),
        )
    except Exception as e:
        logger.exception("DALL-E generation failed")
        return DalleGenerateImageResponse(
            success=False, error=f"DALL-E generation failed: {str(e)}"
        )
