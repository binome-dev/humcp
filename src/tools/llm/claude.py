from __future__ import annotations

import logging
from typing import Any

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool

try:
    from anthropic import AsyncAnthropic
except ImportError as err:
    raise ImportError(
        "anthropic is required for Claude tools. Install with: pip install anthropic"
    ) from err

logger = logging.getLogger("humcp.tools.llm.claude")


@tool()
async def claude_chat(
    prompt: str,
    system_prompt: str = "",
    model: str = "claude-sonnet-4-20250514",
    temperature: float = 1.0,
    max_tokens: int = 1024,
    top_p: float | None = None,
    top_k: int | None = None,
    stop_sequences: list[str] | None = None,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: dict[str, Any] | None = None,
    response_format: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict:
    """
    Generate a response using Anthropic's Claude API.

    Supports text generation, tool use, and structured JSON output.

    Args:
        prompt: The user message to send to Claude.
        system_prompt: Optional system prompt to guide Claude's behavior.
        model: The Claude model to use.
        temperature: Sampling temperature (0.0 to 1.0).
        max_tokens: Maximum number of tokens to generate.
        top_p: Nucleus sampling threshold (0.0 to 1.0). Use instead of temperature.
        top_k: Sample from top K tokens at each step.
        stop_sequences: Custom text sequences that cause the model to stop generating.
        tools: List of tool definitions. Each dict should have "name", "description",
            and "input_schema" (JSON Schema object). Optionally set "strict": true
            for guaranteed schema-compliant inputs.
        tool_choice: Controls tool use: {"type": "auto"}, {"type": "any"},
            {"type": "tool", "name": "..."}, or {"type": "none"}.
        response_format: JSON Schema for structured output. Passed as
            output_config.format with type "json_schema".
            Example: {"type": "object", "properties": {...}, "required": [...]}.
        extra: Additional keyword arguments passed directly to
            client.messages.create(). Use for any API parameters not
            explicitly listed (e.g. metadata, thinking, service_tier).

    Returns:
        Success flag with model response data or error message.
    """
    try:
        api_key = await resolve_credential("ANTHROPIC_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "ANTHROPIC_API_KEY is not set.",
            }

        logger.info("Claude chat start model=%s", model)
        client = AsyncAnthropic(api_key=api_key)

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if top_p is not None:
            kwargs["top_p"] = top_p
        if top_k is not None:
            kwargs["top_k"] = top_k
        if stop_sequences:
            kwargs["stop_sequences"] = stop_sequences
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
        if response_format:
            kwargs["output_config"] = {
                "format": {"type": "json_schema", "schema": response_format}
            }
        if extra:
            kwargs.update(extra)

        response = await client.messages.create(**kwargs)

        content = "".join(
            block.text for block in response.content if block.type == "text"
        )

        tool_calls = [
            {
                "id": block.id,
                "name": block.name,
                "input": block.input,
            }
            for block in response.content
            if block.type == "tool_use"
        ]

        data: dict[str, Any] = {
            "model": response.model,
            "content": content,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        }
        if tool_calls:
            data["tool_calls"] = tool_calls

        return {"success": True, "data": data}
    except Exception as e:
        logger.exception("Claude chat failed")
        return {"success": False, "error": f"Claude chat failed: {e}"}
