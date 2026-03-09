from __future__ import annotations

import logging
from typing import Any

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool

try:
    from google import genai
    from google.genai import types
except ImportError as err:
    raise ImportError(
        "google-genai is required for Gemini tools. Install with: pip install google-genai"
    ) from err

logger = logging.getLogger("humcp.tools.llm.gemini")


@tool()
async def gemini_chat(
    prompt: str,
    system_prompt: str = "",
    model: str = "gemini-2.5-flash",
    temperature: float = 1.0,
    max_tokens: int = 1024,
    top_p: float | None = None,
    top_k: int | None = None,
    stop_sequences: list[str] | None = None,
    frequency_penalty: float | None = None,
    presence_penalty: float | None = None,
    tools: list[dict[str, Any]] | None = None,
    tool_config: dict[str, Any] | None = None,
    response_format: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict:
    """
    Generate a response using Google's Gemini API.

    Supports text generation, function calling, and structured JSON output.

    Args:
        prompt: The user message to send to Gemini.
        system_prompt: Optional system instruction to guide Gemini's behavior.
        model: The Gemini model to use.
        temperature: Sampling temperature (0.0 to 2.0).
        max_tokens: Maximum number of tokens to generate.
        top_p: Nucleus sampling threshold (0.0 to 1.0).
        top_k: Sample from top K tokens at each step.
        stop_sequences: Strings that cause the model to stop generating.
        frequency_penalty: Penalize tokens by frequency (-2.0 to 2.0).
        presence_penalty: Penalize tokens already present (-2.0 to 2.0).
        tools: List of function declarations. Each dict should have "name",
            "description", and "parameters" (JSON Schema object). These are
            wrapped into a Tool with function_declarations.
        tool_config: Controls function calling behavior. Example:
            {"function_calling_config": {"mode": "ANY",
            "allowed_function_names": ["..."]}}.
            Modes: "AUTO", "ANY", "NONE", "VALIDATED".
        response_format: JSON Schema for structured output. When provided,
            sets response_mime_type to "application/json" and passes the
            schema via response_json_schema.
        extra: Additional keyword arguments passed directly to
            GenerateContentConfig. Use for any config parameters not
            explicitly listed (e.g. safety_settings, thinking_config,
            candidate_count, seed).

    Returns:
        Success flag with model response data or error message.
    """
    try:
        api_key = await resolve_credential("GOOGLE_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "GOOGLE_API_KEY is not set.",
            }

        logger.info("Gemini chat start model=%s", model)
        client = genai.Client(api_key=api_key)

        config_kwargs: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt
        if top_p is not None:
            config_kwargs["top_p"] = top_p
        if top_k is not None:
            config_kwargs["top_k"] = top_k
        if stop_sequences:
            config_kwargs["stop_sequences"] = stop_sequences
        if frequency_penalty is not None:
            config_kwargs["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            config_kwargs["presence_penalty"] = presence_penalty
        if tools:
            config_kwargs["tools"] = [types.Tool(function_declarations=tools)]
        if tool_config:
            config_kwargs["tool_config"] = tool_config
        if response_format:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_json_schema"] = response_format
        if extra:
            config_kwargs.update(extra)

        config = types.GenerateContentConfig(**config_kwargs)

        response = await client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )

        content = response.text or ""

        tool_calls = None
        if response.function_calls:
            tool_calls = [
                {
                    "name": fc.name,
                    "args": dict(fc.args) if fc.args else {},
                    **({"id": fc.id} if fc.id else {}),
                }
                for fc in response.function_calls
            ]

        finish_reason = None
        if response.candidates and response.candidates[0].finish_reason:
            finish_reason = response.candidates[0].finish_reason.name

        usage_meta = response.usage_metadata
        usage: dict[str, Any] = {}
        if usage_meta:
            usage = {
                "prompt_tokens": usage_meta.prompt_token_count,
                "completion_tokens": usage_meta.candidates_token_count,
                "total_tokens": usage_meta.total_token_count,
            }

        data: dict[str, Any] = {
            "model": model,
            "content": content,
            "finish_reason": finish_reason,
            "usage": usage,
        }
        if tool_calls:
            data["tool_calls"] = tool_calls

        return {"success": True, "data": data}
    except Exception as e:
        logger.exception("Gemini chat failed")
        return {"success": False, "error": f"Gemini chat failed: {e}"}
