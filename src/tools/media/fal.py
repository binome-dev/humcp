"""Fal.ai model execution tool for media generation."""

from __future__ import annotations

import logging
import os
from typing import Any

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.media.schemas import (
    FalOutput,
    FalRunData,
    FalRunResponse,
)

logger = logging.getLogger("humcp.tools.fal")


@tool()
async def fal_run_model(
    model_id: str,
    input_data: dict[str, Any] | None = None,
) -> FalRunResponse:
    """Run an AI model on Fal.ai for media generation.

    Args:
        model_id: The Fal model identifier (e.g., "fal-ai/hunyuan-video",
            "fal-ai/flux/dev").
        input_data: Input parameters for the model as a dictionary.
            Typically includes "prompt" and model-specific options.

    Returns:
        Generated media URLs and their types.
    """
    try:
        fal_key = await resolve_credential("FAL_KEY")
        if not fal_key:
            return FalRunResponse(
                success=False,
                error="Fal API not configured. Set FAL_KEY environment variable.",
            )

        if not model_id.strip():
            return FalRunResponse(success=False, error="Model ID must not be empty.")

        try:
            import fal_client
        except ImportError:
            return FalRunResponse(
                success=False,
                error="fal-client package is required. Install with: pip install fal-client",
            )

        resolved_input = input_data if input_data is not None else {}

        logger.info("Fal run model=%s", model_id)

        os.environ["FAL_KEY"] = fal_key

        seen_logs: set[str] = set()

        def on_queue_update(update: Any) -> None:
            if hasattr(fal_client, "InProgress") and isinstance(
                update, fal_client.InProgress
            ):
                if hasattr(update, "logs") and update.logs:
                    for log_entry in update.logs:
                        message = (
                            log_entry.get("message", "")
                            if isinstance(log_entry, dict)
                            else str(log_entry)
                        )
                        if message not in seen_logs:
                            logger.info("Fal progress: %s", message)
                            seen_logs.add(message)

        result = fal_client.subscribe(
            model_id,
            arguments=resolved_input,
            with_logs=True,
            on_queue_update=on_queue_update,
        )

        outputs = []

        if isinstance(result, dict):
            if "image" in result:
                url = result.get("image", {}).get("url", "")
                if url:
                    outputs.append(FalOutput(url=url, media_type="image"))
            elif "images" in result:
                for img in result.get("images", []):
                    url = img.get("url", "") if isinstance(img, dict) else ""
                    if url:
                        outputs.append(FalOutput(url=url, media_type="image"))
            elif "video" in result:
                url = result.get("video", {}).get("url", "")
                if url:
                    outputs.append(FalOutput(url=url, media_type="video"))

            if not outputs:
                logger.warning(
                    "Fal returned unrecognized result structure keys=%s",
                    list(result.keys()),
                )
                return FalRunResponse(
                    success=False,
                    error=f"Unrecognized output format from model. Keys: {list(result.keys())}",
                )

        logger.info("Fal run complete outputs=%d", len(outputs))

        return FalRunResponse(
            success=True,
            data=FalRunData(
                model_id=model_id,
                outputs=outputs,
            ),
        )
    except Exception as e:
        logger.exception("Fal run failed")
        return FalRunResponse(success=False, error=f"Fal run failed: {str(e)}")
