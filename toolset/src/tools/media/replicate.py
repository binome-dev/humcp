"""Replicate tools for running AI models and checking predictions."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from src.humcp.decorator import tool
from src.tools.media.schemas import (
    ReplicateOutput,
    ReplicatePredictionData,
    ReplicatePredictionResponse,
    ReplicateRunData,
    ReplicateRunResponse,
    ReplicateSearchData,
    ReplicateSearchModelItem,
    ReplicateSearchResponse,
)

logger = logging.getLogger("humcp.tools.replicate")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"}


def _classify_media(url: str) -> str:
    """Determine media type from URL file extension."""
    parsed = urlparse(url)
    ext = Path(parsed.path).suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return "unknown"


@tool()
async def replicate_run_model(
    model: str,
    input_data: dict[str, Any] | None = None,
) -> ReplicateRunResponse:
    """Run an AI model on Replicate and return generated media.

    Args:
        model: The model identifier (e.g., "stability-ai/sdxl", "minimax/video-01").
        input_data: Input parameters for the model as a dictionary.
            Typically includes "prompt" and model-specific options.

    Returns:
        Generated media URLs and their types.
    """
    try:
        api_token = os.getenv("REPLICATE_API_TOKEN")
        if not api_token:
            return ReplicateRunResponse(
                success=False,
                error="Replicate API not configured. Set REPLICATE_API_TOKEN environment variable.",
            )

        if not model.strip():
            return ReplicateRunResponse(
                success=False, error="Model identifier must not be empty."
            )

        try:
            import replicate as replicate_pkg
        except ImportError:
            return ReplicateRunResponse(
                success=False,
                error="replicate package is required. Install with: pip install replicate",
            )

        resolved_input = input_data if input_data is not None else {}

        logger.info("Replicate run model=%s", model)

        os.environ["REPLICATE_API_TOKEN"] = api_token
        raw_output = replicate_pkg.run(ref=model, input=resolved_input)

        from replicate.helpers import FileOutput

        if isinstance(raw_output, FileOutput):
            output_list = [raw_output]
        elif hasattr(raw_output, "__iter__") and not isinstance(raw_output, str):
            output_list = list(raw_output)
        else:
            return ReplicateRunResponse(
                success=False,
                error=f"Unexpected output type: {type(raw_output).__name__}",
            )

        outputs = []
        for item in output_list:
            if isinstance(item, FileOutput):
                url = str(item.url)
                media_type = _classify_media(url)
                outputs.append(ReplicateOutput(url=url, media_type=media_type))
            elif isinstance(item, str):
                media_type = _classify_media(item)
                outputs.append(ReplicateOutput(url=item, media_type=media_type))

        logger.info("Replicate run complete outputs=%d", len(outputs))

        return ReplicateRunResponse(
            success=True,
            data=ReplicateRunData(
                model=model,
                outputs=outputs,
            ),
        )
    except Exception as e:
        logger.exception("Replicate run failed")
        return ReplicateRunResponse(
            success=False, error=f"Replicate run failed: {str(e)}"
        )


@tool()
async def replicate_get_prediction(
    prediction_id: str,
) -> ReplicatePredictionResponse:
    """Check the status of a Replicate prediction.

    Args:
        prediction_id: The prediction ID to check.

    Returns:
        Prediction status, output URLs (if completed), or error details.
    """
    try:
        api_token = os.getenv("REPLICATE_API_TOKEN")
        if not api_token:
            return ReplicatePredictionResponse(
                success=False,
                error="Replicate API not configured. Set REPLICATE_API_TOKEN environment variable.",
            )

        if not prediction_id.strip():
            return ReplicatePredictionResponse(
                success=False, error="Prediction ID must not be empty."
            )

        try:
            import replicate as replicate_pkg
        except ImportError:
            return ReplicatePredictionResponse(
                success=False,
                error="replicate package is required. Install with: pip install replicate",
            )

        logger.info("Replicate get prediction id=%s", prediction_id)

        os.environ["REPLICATE_API_TOKEN"] = api_token
        client = replicate_pkg.Client(api_token=api_token)
        prediction = client.predictions.get(prediction_id)

        output = None
        if prediction.output:
            if isinstance(prediction.output, list):
                output = [str(item) for item in prediction.output]
            else:
                output = [str(prediction.output)]

        error_msg = str(prediction.error) if prediction.error else None

        logger.info("Replicate prediction status=%s", prediction.status)

        return ReplicatePredictionResponse(
            success=True,
            data=ReplicatePredictionData(
                prediction_id=prediction_id,
                status=prediction.status,
                output=output,
                error=error_msg,
            ),
        )
    except Exception as e:
        logger.exception("Replicate get prediction failed")
        return ReplicatePredictionResponse(
            success=False, error=f"Replicate get prediction failed: {str(e)}"
        )


REPLICATE_API_BASE = "https://api.replicate.com/v1"


@tool()
async def replicate_search_models(
    query: str,
) -> ReplicateSearchResponse:
    """Search for AI models on Replicate by keyword.

    Args:
        query: The search query string (e.g., "image generation", "text to speech").

    Returns:
        List of matching models with owner, name, description, and run count.
    """
    try:
        api_token = os.getenv("REPLICATE_API_TOKEN")
        if not api_token:
            return ReplicateSearchResponse(
                success=False,
                error="Replicate API not configured. Set REPLICATE_API_TOKEN environment variable.",
            )

        if not query.strip():
            return ReplicateSearchResponse(
                success=False, error="Query must not be empty."
            )

        headers = {
            "Authorization": f"Bearer {api_token}",
        }

        params = {
            "query": query,
        }

        logger.info("Replicate search models query=%s", query)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{REPLICATE_API_BASE}/models",
                headers=headers,
                params=params,
            )
            response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        models = []
        for item in results:
            models.append(
                ReplicateSearchModelItem(
                    owner=item.get("owner", ""),
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    url=item.get(
                        "url",
                        f"https://replicate.com/{item.get('owner', '')}/{item.get('name', '')}",
                    ),
                    run_count=item.get("run_count", 0),
                )
            )

        logger.info("Replicate search complete results=%d", len(models))

        return ReplicateSearchResponse(
            success=True,
            data=ReplicateSearchData(
                query=query,
                models=models,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception(
            "Replicate search HTTP error status=%d", e.response.status_code
        )
        return ReplicateSearchResponse(
            success=False, error=f"Replicate API error: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("Replicate search models failed")
        return ReplicateSearchResponse(
            success=False, error=f"Replicate search failed: {str(e)}"
        )
