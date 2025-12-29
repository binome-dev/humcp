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

# Docker
docker compose up --build
```

## Architecture

HuMCP is a FastMCP server with a FastAPI adapter that exposes MCP tools as REST endpoints.

### Core Components

**Entry Points:**
- `src/main.py` - FastAPI application that mounts MCP at `/mcp` and auto-generates REST endpoints
- `src/mcp_register.py` - Creates the FastMCP server, auto-discovers and registers tools from `src/tools/`

**Adapter Layer (`src/adapter/`):**
- `fast_mcp_fast_api_adapter.py` - `FastMCPFastAPIAdapter` bridges FastMCP and FastAPI
- `routes.py` - `RouteGenerator` creates REST endpoints from MCP tool schemas
- `models.py` - Dynamically generates Pydantic models from MCP tool input schemas

**Tool Registration System:**
- Tools use `@tool(name, category)` decorator from `src/tools/__init__.py`
- Decorator adds tools to `TOOL_REGISTRY` for auto-discovery
- `src/mcp_register.py` walks `src/tools/` modules and registers all decorated functions with FastMCP

### Adding New Tools

1. Create a `.py` file anywhere under `src/tools/` (no `__init__.py` required)
2. Import and use the `@tool` decorator:
```python
from src.tools import tool

@tool("my_tool_name")
async def my_tool(param: str) -> dict:
    """Tool description."""
    return {"success": True, "data": result}
```
3. Tools are auto-discovered on server startup via filesystem scan - no manual registration needed

### Tool Response Pattern

Tools return `{"success": True, "data": ...}` or `{"success": False, "error": "..."}`.
