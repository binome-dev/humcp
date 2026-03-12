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

- **`server.py`** - `create_app()` creates FastAPI app, loads tool modules, discovers MCP Apps, registers with FastMCP, mounts MCP/REST/OAuth routes
- **`decorator.py`** - `@tool(category="...", app="...")` marks functions for discovery. Category auto-detects from parent folder, `app` defaults to filename stem. Tool name = function name
- **`registry.py`** - `RegisteredTool` NamedTuple wraps FastMCP's `FunctionTool` with `category` and `app` fields
- **`routes.py`** - Generates REST endpoints from registered tools using `FunctionTool.parameters`
- **`config.py`** - Tool filtering via `config/tools.yaml` (include/exclude with wildcard support)
- **`skills.py`** - Discovers `SKILL.md` files for category metadata
- **`schemas.py`** - Pydantic response models for API endpoints
- **`credentials.py`** - `resolve_credential("KEY_NAME")` resolves credentials from env vars
- **`storage_path.py`** - `minio://` URL resolution utilities. `is_storage_path()`, `parse_storage_path()`, `resolve_path()` (async context manager that downloads storage objects to temp files)
- **`auth.py`** - Google OAuth provider via `create_auth_provider()`, `is_auth_enabled()`, `get_current_user_id()` (resolves user from MCP access token or REST ContextVar)
- **`middleware.py`** - `APIKeyMiddleware` validates `X-API-Key` header for REST requests. Extracts user identity from Bearer JWT into ContextVar. Public paths (`/`, `/docs`, `/playground`, etc.) are exempt
- **`permissions.py`** - `require_auth()` returns user UUID or raises 401 when `TOOLSET_REQUIRE_AUTH=true`. `check_permission()` is a stub that delegates to `require_auth()` (upgrade to full IAM when available). `STRICT_PERMISSIONS=true` rejects all permission checks
- **`playground.py`** - `get_playground_html()` returns a self-contained HTML page for interactive tool browsing and execution at `/playground`

### Authentication Modes

The server supports four auth modes, selected by environment variables:

1. **JWT mode** - Set `JWT_SECRET_KEY`: uses `JWTVerifier` for MCP auth (service-to-service). Middleware decodes Bearer JWTs on REST requests
2. **Google OAuth** - Set `GOOGLE_OAUTH_CLIENT_ID` + `GOOGLE_OAUTH_CLIENT_SECRET` + `AUTH_ENABLED=true`: `GoogleProvider` handles browser login flow with Google scopes (Gmail, Calendar, Drive, Tasks, Docs, Sheets, etc.)
3. **API key** - Set `SERVICE_API_KEY`: `APIKeyMiddleware` requires `X-API-Key` header on all non-public REST requests. Uses constant-time comparison
4. **No auth** - Default dev mode when none of the above are configured

### Tool Discovery Flow

1. `create_app()` loads Python modules from `src/tools/` recursively
2. Functions with `@tool()` decorator are discovered via `_humcp_tool` attribute
3. Each tool is registered with FastMCP via `mcp.tool()(func)` which creates a `FunctionTool`
4. `RegisteredTool(tool=fn_tool, category=..., app=...)` pairs the FunctionTool with its category and app
5. REST routes are generated from `FunctionTool.parameters` (JSON Schema)
6. Tools are filtered by `config/tools.yaml` before route registration

### Tool Categories (24)

api, audio, builder, calendar, cloud, data, database, ecommerce, files, finance, google, image, llm, local, media, memory, messaging, project_management, research, search, social, storage, weather, web_scraping

### App Grouping

The `@tool()` decorator accepts an `app` parameter (defaults to the filename stem). `RegisteredTool` carries this `app` field. REST responses include `apps` grouping so clients can group related tools by their source module.

### Adding New Tools

Create a `.py` file in `src/tools/<category>/`:

```python
from src.humcp.decorator import tool

@tool()  # category auto-detected from folder name, app from filename
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

### MCP Apps System

Interactive UI panels rendered alongside tool results:

- HTML bundles live in `src/apps/{category}/{tool_name}.html`
- Registered as `ui://` MCP resources on the FastMCP server
- Served via `/apps/{tool_name}` REST endpoint and listed at `/apps`
- Claude.ai renders them as interactive UI panels via iframe + JSON-RPC messaging (`ui/ready`, `ui/initialize`, `ui/toolResult`)
- The Playground (`/playground`) also renders app HTML for tools that have them

### Builder Subsystem

Custom tool creation at runtime (`src/tools/builder/`):

- `tools.py` - `tool_builder_*` functions for creating, listing, updating, deleting custom tools
- `sandbox.py` - Sandboxed execution via RestrictedPython
- `storage.py` - Persistence for custom tool definitions
- `schemas.py` - Pydantic models for builder requests
- All builder endpoints require authentication

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

### Key Environment Variables

| Variable | Purpose |
|---|---|
| `MCP_SERVER_URL` | Advertised MCP endpoint URL (default `http://0.0.0.0:8080/mcp`) |
| `AUTH_ENABLED` | Enable/disable Google OAuth (default `true`) |
| `JWT_SECRET_KEY` | Enables JWT auth mode for MCP and REST Bearer tokens |
| `SERVICE_API_KEY` | Enables API key middleware for REST endpoints |
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth client secret |
| `TOOLSET_REQUIRE_AUTH` | When `true`, `require_auth()` raises 401 for unauthenticated requests |
| `STRICT_PERMISSIONS` | When `true`, `check_permission()` rejects all calls (no IAM backend) |
| `STORAGE_ENDPOINT` | MinIO/S3 storage endpoint |
| `STORAGE_ACCESS_KEY` | MinIO/S3 access key |
| `STORAGE_SECRET_KEY` | MinIO/S3 secret key |
| `STORAGE_SECURE` | Use HTTPS for storage connections |
| `DB_READ_ONLY` | Database read-only mode (default `true`) |
| `HTTP_ALLOW_PRIVATE` | Allow HTTP requests to private IPs (default `false`) |
