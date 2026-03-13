from __future__ import annotations

import logging
import os
from typing import Any

from src.humcp.decorator import tool

try:
    from ollama import AsyncClient
except ImportError as err:
    raise ImportError(
        "ollama is required for Ollama tools. Install with: pip install ollama"
    ) from err

logger = logging.getLogger("humcp.tools.llm.ollama")


@tool()
async def ollama_chat(
    prompt: str,
    system_prompt: str = "",
    model: str = "llama3.2",
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    stop: list[str] | None = None,
    seed: int | None = None,
    frequency_penalty: float | None = None,
    presence_penalty: float | None = None,
    tools: list[dict[str, Any]] | None = None,
    response_format: str | dict[str, Any] | None = None,
    host: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict:
    """
    Generate a response using a local or remote Ollama server.

    Supports text generation, tool calling, and structured JSON output.

    Args:
        prompt: The user message to send to the model.
        system_prompt: Optional system prompt to guide the model's behavior.
        model: The Ollama model to use (e.g. "llama3.2", "gemma3", "qwen3").
        temperature: Sampling temperature. Higher = more creative.
        max_tokens: Maximum number of tokens to generate (maps to num_predict).
        top_p: Nucleus sampling threshold (0.0 to 1.0).
        top_k: Sample from top K tokens at each step.
        stop: Sequences that cause the model to stop generating.
        seed: Random seed for reproducible output.
        frequency_penalty: Penalize tokens by frequency of appearance.
        presence_penalty: Penalize tokens that have already appeared.
        tools: List of tool definitions. Each dict should have "type": "function"
            and a "function" key with "name", "description", "parameters"
            (JSON Schema object).
        response_format: Constrain output format. Use "json" for JSON mode, or
            a JSON Schema dict for schema-enforced structured output.
        host: Ollama server URL. Defaults to OLLAMA_HOST env var or
            http://localhost:11434.
        extra: Additional keyword arguments passed directly to
            client.chat(). Use for any parameters not explicitly listed
            (e.g. think, keep_alive, logprobs).

    Returns:
        Success flag with model response data or error message.
    """
    try:
        resolved_host = host or os.getenv("OLLAMA_HOST")
        client_kwargs: dict[str, Any] = {}
        if resolved_host:
            client_kwargs["host"] = resolved_host

        logger.info("Ollama chat start model=%s", model)
        client = AsyncClient(**client_kwargs)

        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        options: dict[str, Any] = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if top_p is not None:
            options["top_p"] = top_p
        if top_k is not None:
            options["top_k"] = top_k
        if stop:
            options["stop"] = stop
        if seed is not None:
            options["seed"] = seed
        if frequency_penalty is not None:
            options["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            options["presence_penalty"] = presence_penalty

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if options:
            kwargs["options"] = options
        if tools:
            kwargs["tools"] = tools
        if response_format is not None:
            kwargs["format"] = response_format
        if extra:
            kwargs.update(extra)

        response = await client.chat(**kwargs)

        content = response.message.content or ""

        tool_calls = None
        if response.message.tool_calls:
            tool_calls = [
                {
                    "name": tc.function.name,
                    "arguments": dict(tc.function.arguments),
                }
                for tc in response.message.tool_calls
            ]

        usage: dict[str, Any] = {}
        if response.prompt_eval_count is not None:
            usage["prompt_tokens"] = response.prompt_eval_count
        if response.eval_count is not None:
            usage["completion_tokens"] = response.eval_count
            if response.prompt_eval_count is not None:
                usage["total_tokens"] = response.prompt_eval_count + response.eval_count

        data: dict[str, Any] = {
            "model": response.model,
            "content": content,
            "done_reason": response.done_reason,
            "usage": usage,
        }
        if tool_calls:
            data["tool_calls"] = tool_calls

        return {"success": True, "data": data}
    except Exception as e:
        logger.exception("Ollama chat failed")
        return {"success": False, "error": f"Ollama chat failed: {e}"}
