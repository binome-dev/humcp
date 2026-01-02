# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run server locally
uv run uvicorn src.main:app --host 0.0.0.0 --port 8080

# Run tests
uv run pytest

# Run a single test file
uv run pytest tests/tools/local/test_calculator.py

# Run a specific test
uv run pytest tests/tools/local/test_calculator.py::test_add -v

# Linting
uv run ruff check

# Type checking
uv run mypy src/

# Pre-commit hooks
uv run pre-commit run --all-files

# Docker
docker compose up --build
```

## Architecture

HuMCP exposes tools via both MCP (Model Context Protocol) at `/mcp` and REST at `/tools/*`.

### Core Library (`src/humcp/`)

- **`server.py`** - `create_app()` creates FastAPI app, loads tool modules, registers with FastMCP
- **`decorator.py`** - `@tool(category="...")` marks functions for discovery. Category auto-detects from parent folder if not specified. Tool name = function name (used by FastMCP)
- **`registry.py`** - `RegisteredTool` NamedTuple wraps FastMCP's `FunctionTool` with category
- **`routes.py`** - Generates REST endpoints from registered tools using `FunctionTool.parameters`
- **`config.py`** - Tool filtering via `config/tools.yaml` (include/exclude with wildcard support)
- **`skills.py`** - Discovers `SKILL.md` files for category metadata
- **`schemas.py`** - Pydantic response models for API endpoints

### Tool Discovery Flow

1. `create_app()` loads Python modules from `src/tools/` recursively
2. Functions with `@tool()` decorator are discovered via `_humcp_tool` attribute
3. Each tool is registered with FastMCP via `mcp.tool()(func)` which creates a `FunctionTool`
4. `RegisteredTool(tool=fn_tool, category=...)` pairs the FunctionTool with its category
5. REST routes are generated from `FunctionTool.parameters` (JSON Schema)

### Adding New Tools

Create a `.py` file in `src/tools/<category>/`:

```python
from src.humcp.decorator import tool

@tool()  # category auto-detected from folder name
async def my_tool(param: str) -> dict:
    """Tool description (used by FastMCP and Swagger)."""
    return {"success": True, "data": {"result": param}}
```

The function name becomes the tool name. Tools are auto-discovered on server startup.

### Response Pattern

```python
# Success
return {"success": True, "data": {...}}

# Error
return {"success": False, "error": "Error message"}
```

### Skills

Add `SKILL.md` in tool category folders with YAML frontmatter:

```markdown
---
name: skill-name
description: When and how to use these tools
---
# Content for AI assistants
```

### Tool Configuration

`config/tools.yaml` controls which tools are exposed:

```yaml
include:
  categories: [local, data]
  tools: [tavily_web_search]
exclude:
  tools: [shell_*]  # wildcards supported
```

Empty config = load all tools.
