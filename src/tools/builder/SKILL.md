---
name: custom-tool-builder
description: Create custom tools with sandboxed Python code. Use when you need to define new tools dynamically without modifying the codebase.
---

# Tool Builder

Create and manage custom tools with sandboxed Python execution.

## Overview

The tool builder allows you to create new tools by providing Python code that runs in a secure sandbox. Custom tools can be enabled to become first-class MCP/REST tools.

## Creating a Custom Tool

```python
result = await tool_builder_create(
    name="text_processor",
    description="Process text with various transformations",
    parameters={
        "text": {"type": "string", "description": "Input text"},
        "uppercase": {"type": "boolean", "default": False}
    },
    code='''
def execute(text: str, uppercase: bool = False) -> dict:
    result = text.upper() if uppercase else text.lower()
    return {"success": True, "data": {"result": result}}
''',
    category="custom"
)
```

### Code Requirements

1. Must define an `execute` function
2. Function must return a dict with `success` and `data`/`error` keys
3. Code runs in a sandboxed environment with limited capabilities

## Testing a Custom Tool

Before enabling, test your tool:

```python
result = await tool_builder_test(
    name="text_processor",
    params={"text": "Hello World", "uppercase": True}
)
# Returns: {"success": True, "data": {"tool_name": "text_processor", "result": {...}}}
```

## Enabling/Disabling Tools

Tools are created disabled. Enable to make them available via MCP/REST:

```python
# Enable - registers with MCP
await tool_builder_enable(name="text_processor")

# Disable - unregisters from MCP
await tool_builder_disable(name="text_processor")
```

## Managing Custom Tools

```python
# List all custom tools
result = await tool_builder_list()

# Get tool details
result = await tool_builder_get(name="text_processor")

# Update tool code or description
result = await tool_builder_update(
    name="text_processor",
    description="Updated description",
    code="def execute(): return {'success': True, 'data': {}}"
)

# Delete a tool
result = await tool_builder_delete(name="text_processor")
```

## Sandbox Environment

### Allowed

- Basic Python: variables, functions, loops, conditionals
- Type constructors: `list`, `dict`, `set`, `str`, `int`, `float`, etc.
- Utility functions: `len`, `range`, `sorted`, `min`, `max`, `sum`, etc.
- Allowed imports: `json`, `re`, `math`, `datetime`

### Blocked

- File system access: `open`, `os`, `pathlib`
- Network access: `socket`, `requests`, `httpx`
- System calls: `subprocess`, `os.system`
- Dangerous builtins: `exec`, `eval`, `compile`, `__import__`
- Module imports (except allowlist)

### Execution Limits

- **Timeout**: 60 seconds maximum execution time
- **Memory**: No hard limit (Python process limit applies)

## Example: JSON Transformer

```python
await tool_builder_create(
    name="json_transform",
    description="Transform JSON data by extracting specific fields",
    parameters={
        "data": {"type": "object", "description": "Input JSON object"},
        "fields": {"type": "array", "description": "Fields to extract"}
    },
    code='''
def execute(data: dict, fields: list) -> dict:
    result = {field: data.get(field) for field in fields if field in data}
    return {"success": True, "data": result}
'''
)
```

## Example: Text Statistics

```python
await tool_builder_create(
    name="text_stats",
    description="Calculate statistics about text",
    parameters={
        "text": {"type": "string", "description": "Input text"}
    },
    code='''
def execute(text: str) -> dict:
    words = text.split()
    return {
        "success": True,
        "data": {
            "char_count": len(text),
            "word_count": len(words),
            "line_count": text.count("\\n") + 1,
            "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0
        }
    }
'''
)
```

## Response Format

All tools return:
```json
{
  "success": true,
  "data": {
    "name": "my_tool",
    "description": "...",
    "code": "...",
    "parameters": {...},
    "category": "custom",
    "enabled": false,
    "created_at": "2026-01-03T...",
    "updated_at": "2026-01-03T..."
  }
}
```

On error:
```json
{
  "success": false,
  "error": "Error description"
}
```
