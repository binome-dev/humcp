"""NanoBanana/Banana.dev AI model execution tool."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from src.humcp.decorator import tool
from src.tools.media.schemas import (
    NanoBananaRunData,
    NanoBananaRunResponse,
)

logger = logging.getLogger("humcp.tools.nano_banana")

BANANA_API_URL = "https://api.banana.dev/start/v4"
BANANA_CHECK_URL = "https://api.banana.dev/check/v4"


@tool()
async def nano_banana_run(
    model_name: str,
    input_data: dict[str, Any] | None = None,
) -> NanoBananaRunResponse:
    """Run an AI model on NanoBanana/Banana.dev and return generated outputs.

    Args:
        model_name: The model key or name to run on Banana.dev.
        input_data: Input parameters for the model as a dictionary.
            Contents depend on the specific model being run.

    Returns:
        Generated output URLs and status.
    """
    try:
        api_key = os.getenv("BANANA_API_KEY")
        if not api_key:
            return NanoBananaRunResponse(
                success=False,
                error="Banana API not configured. Set BANANA_API_KEY environment variable.",
            )

        if not model_name.strip():
            return NanoBananaRunResponse(
                success=False, error="Model name must not be empty."
            )

        resolved_input = input_data if input_data is not None else {}

        payload = {
            "apiKey": api_key,
            "modelKey": model_name,
            "modelInputs": resolved_input,
        }

        logger.info("NanoBanana run model=%s", model_name)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                BANANA_API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

        result = response.json()

        call_id = result.get("callID", "")
        message = result.get("message", "")

        if message and "error" in message.lower():
            logger.error("NanoBanana error: %s", message)
            return NanoBananaRunResponse(
                success=False, error=f"NanoBanana error: {message}"
            )

        model_outputs = result.get("modelOutputs", [])
        output_urls = []
        for output in model_outputs:
            if isinstance(output, dict):
                url = (
                    output.get("url")
                    or output.get("image_url")
                    or output.get("video_url")
                )
                if url:
                    output_urls.append(url)
            elif isinstance(output, str):
                output_urls.append(output)

        status = "completed" if model_outputs else "processing"

        logger.info(
            "NanoBanana run complete call_id=%s outputs=%d status=%s",
            call_id,
            len(output_urls),
            status,
        )

        return NanoBananaRunResponse(
            success=True,
            data=NanoBananaRunData(
                model_name=model_name,
                output_urls=output_urls,
                status=status,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("NanoBanana HTTP error status=%d", e.response.status_code)
        return NanoBananaRunResponse(
            success=False, error=f"NanoBanana API error: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("NanoBanana run failed")
        return NanoBananaRunResponse(
            success=False, error=f"NanoBanana run failed: {str(e)}"
        )
