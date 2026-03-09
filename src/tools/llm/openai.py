from __future__ import annotations

import json
import logging
from typing import Any

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool

try:
    from openai import AsyncOpenAI
except ImportError as err:
    raise ImportError(
        "openai is required for OpenAI tools. Install with: pip install openai"
    ) from err

logger = logging.getLogger("humcp.tools.llm.openai")


@tool()
async def openai_chat(
    prompt: str,
    system_prompt: str = "",
    model: str = "gpt-4o",
    temperature: float = 1.0,
    max_tokens: int = 1024,
    top_p: float | None = None,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | dict[str, Any] | None = None,
    response_format: dict[str, Any] | None = None,
    store: bool | None = None,
    extra: dict[str, Any] | None = None,
) -> dict:
    """
    Generate a response using OpenAI's Responses API.

    Supports text generation, tool calling (including built-in web_search,
    file_search, code_interpreter), and structured JSON output.

    Args:
        prompt: The user message to send to the model.
        system_prompt: Optional system instructions to guide the model's behavior.
        model: The OpenAI model to use.
        temperature: Sampling temperature (0.0 to 2.0).
        max_tokens: Maximum number of output tokens to generate.
        top_p: Nucleus sampling threshold (0.0 to 1.0). Alternative to temperature.
        tools: List of tool definitions. For function tools use
            {"type": "function", "name": "...", "parameters": {...}}.
            Built-in tools: {"type": "web_search"}, {"type": "file_search", ...},
            {"type": "code_interpreter"}.
        tool_choice: Controls tool use: "auto", "none", "required", or
            {"type": "function", "name": "..."}.
        response_format: Structured output config passed as text.format.
            Use {"type": "json_object"} for JSON mode, or
            {"type": "json_schema", "name": "...", "strict": true,
            "schema": {...}} for schema-enforced output.
        store: Whether to store the response server-side. Defaults to true.
        extra: Additional keyword arguments passed directly to
            client.responses.create(). Use for any API parameters not
            explicitly listed (e.g. reasoning, previous_response_id,
            include, truncation, metadata).

    Returns:
        Success flag with model response data or error message.
    """
    try:
        api_key = await resolve_credential("OPENAI_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "OPENAI_API_KEY is not set.",
            }

        logger.info("OpenAI chat start model=%s", model)
        client = AsyncOpenAI(api_key=api_key)

        kwargs: dict[str, Any] = {
            "model": model,
            "input": prompt,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_prompt:
            kwargs["instructions"] = system_prompt
        if top_p is not None:
            kwargs["top_p"] = top_p
        if tools:
            kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
        if response_format:
            kwargs["text"] = {"format": response_format}
        if store is not None:
            kwargs["store"] = store
        if extra:
            kwargs.update(extra)

        response = await client.responses.create(**kwargs)

        content = response.output_text

        tool_calls = []
        for item in response.output:
            if item.type == "function_call":
                tool_calls.append(
                    {
                        "id": item.call_id,
                        "name": item.name,
                        "arguments": json.loads(item.arguments),
                    }
                )
            elif item.type == "web_search_call":
                tool_calls.append(
                    {
                        "id": item.id,
                        "type": "web_search_call",
                        "status": item.status,
                    }
                )

        usage_data: dict[str, Any] = {}
        if response.usage:
            usage_data = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        data: dict[str, Any] = {
            "id": response.id,
            "model": response.model,
            "content": content,
            "status": response.status,
            "usage": usage_data,
        }
        if tool_calls:
            data["tool_calls"] = tool_calls

        return {"success": True, "data": data}
    except Exception as e:
        logger.exception("OpenAI chat failed")
        return {"success": False, "error": f"OpenAI chat failed: {e}"}
