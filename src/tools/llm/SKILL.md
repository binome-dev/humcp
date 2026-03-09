---
name: llm
description: Generate text, call tools, and get structured JSON output using LLM providers (Claude, OpenAI, Gemini, Ollama). Use when the user needs to call an LLM API for text generation, function calling, or structured data extraction.
---

# LLM Tools

Tools for generating text, calling functions, and extracting structured data using LLM APIs.

## Requirements

Set environment variables for the providers you want to use:
- `ANTHROPIC_API_KEY`: For Claude tools
- `OPENAI_API_KEY`: For OpenAI tools
- `GOOGLE_API_KEY`: For Gemini tools
- `OLLAMA_HOST`: For Ollama (optional, defaults to `http://localhost:11434`)

## Basic Chat

```python
result = await claude_chat(prompt="Explain quantum computing")
result = await openai_chat(prompt="Explain quantum computing")
result = await gemini_chat(prompt="Explain quantum computing")
result = await ollama_chat(prompt="Explain quantum computing")
```

## Tool / Function Calling

### Claude

```python
result = await claude_chat(
    prompt="What's the weather in San Francisco?",
    tools=[{
        "name": "get_weather",
        "description": "Get current weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }],
    tool_choice={"type": "auto"}
)
# result["data"]["tool_calls"] = [{"id": "...", "name": "get_weather", "input": {"location": "San Francisco"}}]
```

### OpenAI (Responses API)

Supports both custom function tools and built-in tools (`web_search`, `file_search`, `code_interpreter`).

```python
# Custom function tool
result = await openai_chat(
    prompt="What's the weather in San Francisco?",
    tools=[{
        "type": "function",
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }],
    tool_choice="auto"
)
# result["data"]["tool_calls"] = [{"id": "...", "name": "get_weather", "arguments": {"location": "San Francisco"}}]

# Built-in web search
result = await openai_chat(
    prompt="What happened in the news today?",
    tools=[{"type": "web_search"}]
)
```

### Gemini

```python
result = await gemini_chat(
    prompt="What's the weather in San Francisco?",
    tools=[{
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }],
    tool_config={"function_calling_config": {"mode": "AUTO"}}
)
# result["data"]["tool_calls"] = [{"name": "get_weather", "args": {"location": "San Francisco"}}]
```

### Ollama

```python
result = await ollama_chat(
    prompt="What's the weather in San Francisco?",
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }]
)
# result["data"]["tool_calls"] = [{"name": "get_weather", "arguments": {"location": "San Francisco"}}]
```

## Structured Output (JSON Schema)

### Claude

```python
result = await claude_chat(
    prompt="Extract: John Smith, john@example.com, Enterprise plan",
    response_format={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
            "plan": {"type": "string"}
        },
        "required": ["name", "email", "plan"]
    }
)
```

### OpenAI

```python
# JSON mode (valid JSON, no schema enforcement)
result = await openai_chat(
    prompt="List 3 colors as JSON",
    system_prompt="Respond in JSON format.",
    response_format={"type": "json_object"}
)

# Structured output (schema-enforced)
result = await openai_chat(
    prompt="Extract: John Smith, john@example.com, Enterprise plan",
    response_format={
        "type": "json_schema",
        "name": "contact_info",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "plan": {"type": "string"}
            },
            "required": ["name", "email", "plan"],
            "additionalProperties": False
        }
    }
)
```

### Gemini

```python
result = await gemini_chat(
    prompt="Extract: John Smith, john@example.com, Enterprise plan",
    response_format={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
            "plan": {"type": "string"}
        },
        "required": ["name", "email", "plan"]
    }
)
```

### Ollama

```python
# JSON mode
result = await ollama_chat(
    prompt="List 3 colors as JSON",
    response_format="json"
)

# Schema-enforced structured output
result = await ollama_chat(
    prompt="Extract: John Smith, john@example.com, Enterprise plan",
    response_format={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
            "plan": {"type": "string"}
        },
        "required": ["name", "email", "plan"]
    }
)
```

## Response Format

All tools return a standardized response:

```json
{
  "success": true,
  "data": {
    "model": "gpt-4o",
    "content": "Generated text...",
    "usage": {"input_tokens": 25, "output_tokens": 150},
    "tool_calls": [{"id": "...", "name": "fn", "arguments": {...}}]
  }
}
```

Provider-specific fields:
- **Claude**: `stop_reason` (`"end_turn"`, `"tool_use"`, `"max_tokens"`)
- **OpenAI**: `id` (response ID for chaining), `status` (`"completed"`, `"failed"`)
- **Gemini**: `finish_reason` (`"STOP"`, `"MAX_TOKENS"`)
- **Ollama**: `done_reason` (`"stop"`, etc.)

## Parameters

| Parameter | Type | Claude | OpenAI | Gemini | Ollama |
|-----------|------|--------|--------|--------|--------|
| prompt | str | Yes | Yes | Yes | Yes |
| system_prompt | str | Yes | Yes | Yes | Yes |
| model | str | Yes | Yes | Yes | Yes |
| temperature | float | 0-1 | 0-2 | 0-2 | Yes |
| max_tokens | int | Yes | Yes | Yes | Yes |
| top_p | float | Yes | Yes | Yes | Yes |
| top_k | int | Yes | - | Yes | Yes |
| stop/stop_sequences | list[str] | Yes | - | Yes | Yes |
| frequency_penalty | float | - | - | Yes | Yes |
| presence_penalty | float | - | - | Yes | Yes |
| seed | int | - | - | - | Yes |
| tools | list[dict] | Yes | Yes | Yes | Yes |
| tool_choice/tool_config | dict/str | Yes | Yes | Yes | - |
| response_format | dict/str | Yes | Yes | Yes | Yes |
| store | bool | - | Yes | - | - |
| host | str | - | - | - | Yes |
| extra | dict | Yes | Yes | Yes | Yes |

The `extra` parameter accepts a dict of additional provider-specific kwargs passed directly to the underlying API call.
