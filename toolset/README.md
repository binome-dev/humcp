# Toolset - HuMCP Server

HuMCP is a tool execution service that exposes tools via both MCP (Model Context Protocol) and REST endpoints with auto-generated Swagger documentation. It's part of the Graphite Workflow Builder monorepo.

## Features

- Simple `@tool` decorator to register tools
- Auto-generated REST endpoints at `/tools/*`
- MCP server at `/mcp` for AI assistant integration
- Auto-generated Swagger/OpenAPI documentation at `/docs`
- MCP Apps: interactive HTML UIs for tool results (auto-discovered from `src/apps/`)
- Tools organized by category with skill metadata
- Configurable tool filtering via YAML config
- Docker Compose setup for easy deployment

## Quick Start

### From Monorepo Root (Recommended)

```bash
# Install all dependencies
make install

# Start the toolset server
make dev-toolset
```

### Standalone

```bash
cd toolset

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env
# Edit .env and add your API keys (Tavily, Google OAuth, etc.)

# Run server
uv run uvicorn src.main:app --host 0.0.0.0 --port 8003
```

### Access Points

| Endpoint | URL |
|----------|-----|
| Swagger UI | http://localhost:8003/docs |
| REST API | http://localhost:8003/tools/* |
| MCP Apps | http://localhost:8003/apps/* |
| MCP endpoint | http://localhost:8003/mcp |

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker & Docker Compose (optional)

---

# Creating Tools

## Adding a New Tool

1. Create a `.py` file in `src/tools/<category>/` (e.g., `src/tools/local/my_tool.py`)
2. Use the `@tool` decorator:

```python
from src.humcp.decorator import tool

@tool()
async def greet(name: str) -> dict:
    """Greet a user by name.

    Args:
        name: The name of the person to greet.

    Returns:
        A greeting message for the specified person.
    """
    return {"success": True, "data": {"message": f"Hello, {name}!"}}
```

3. Start the server - tools are auto-discovered!

## Tool Documentation

**Your docstring becomes the tool's user interface:**

- **REST API**: Appears in Swagger/OpenAPI docs at `/docs`
- **MCP Protocol**: Sent to AI assistants to help them understand when and how to use your tool
- **Type hints**: Combined with docstrings to generate input schemas

### Best Practices

✅ **DO:**
- Write clear, concise docstrings that explain what the tool does
- Document all parameters with their purpose and expected format
- Describe what the tool returns
- Use proper Python type hints

❌ **DON'T:**
- Leave tools without docstrings
- Use vague descriptions like "does stuff"
- Forget to document parameters or return values

### Example

```python
@tool()
async def search_files(pattern: str, directory: str = ".") -> dict:
    """Search for files matching a pattern in a directory.

    Recursively searches the specified directory for files whose names
    match the given pattern (supports wildcards like *.txt).

    Args:
        pattern: File pattern to search for (e.g., "*.py", "config.*")
        directory: Directory to search in (default: current directory)

    Returns:
        List of matching file paths with their sizes and modification times.
    """
    ...
```

## Tool Naming

```python
# Auto-generated name: "{category}_{function_name}"
@tool()
async def greet(name: str) -> dict:
    ...

# Explicit name
@tool("my_custom_tool")
async def greet(name: str) -> dict:
    ...

# Explicit name and category
@tool("my_tool", category="custom")
async def greet(name: str) -> dict:
    ...
```

## Response Pattern

Tools should return a dictionary:

```python
# Success
return {"success": True, "data": {"result": value}}

# Error
return {"success": False, "error": "Error message"}
```

## MCP Apps

MCP Apps render tool results as interactive HTML UIs inside sandboxed iframes. Each app is a standalone HTML file bound to a specific tool and delivered via both REST and MCP transport.

### How It Works

1. HTML files in `src/apps/<category>/<tool_name>.html` are auto-discovered at startup
2. Each app is bound to its matching tool by filename (e.g., `add.html` binds to tool `add`)
3. Apps are served via REST (`GET /apps/{tool_name}`) and registered as MCP `ui://` resources
4. The frontend fetches the HTML through the backend proxy (`GET /api/tools/apps/{tool_name}`), renders it in a sandboxed `<iframe>`, and sends tool result data via `postMessage`

### Creating an App

Create an HTML file at `src/apps/<category>/<tool_name>.html` where the filename matches the tool's registered name (without the category prefix).

**Example:** For a tool function `add` in `src/tools/calculator/add.py`, create `src/apps/calculator/add.html`.

#### Minimal Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>My Tool App</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>body { margin: 0; font-family: system-ui, sans-serif; }</style>
</head>
<body>
  <div id="app" class="p-6">
    <div id="loading" class="text-slate-400 text-sm">Waiting for data...</div>
    <div id="result" class="hidden"><!-- Render results here --></div>
    <div id="error" class="hidden text-red-600 text-sm font-medium"></div>
  </div>

  <script type="module">
    function render(data) {
      document.getElementById('loading').classList.add('hidden');
      document.getElementById('result').classList.remove('hidden');
      // Populate your UI with data
      document.getElementById('result').textContent = JSON.stringify(data);
    }

    function renderError(message) {
      document.getElementById('loading').classList.add('hidden');
      document.getElementById('error').classList.remove('hidden');
      document.getElementById('error').textContent = message;
    }

    function parseToolResult(result) {
      // MCP Apps protocol: content array with text items
      if (result?.content) {
        for (const item of result.content) {
          if (item.type === 'text' && item.text) {
            try { return JSON.parse(item.text); } catch { return { raw: item.text }; }
          }
        }
      }
      return result;
    }

    function handleToolResult(result) {
      const parsed = parseToolResult(result);
      if (parsed?.success === false) {
        renderError(parsed.error || 'Operation failed');
        return;
      }
      render(parsed?.data || parsed);
    }

    // Listen for postMessage from host
    window.addEventListener('message', (event) => {
      const msg = event.data;
      if (!msg || typeof msg !== 'object') return;

      // MCP Apps JSON-RPC protocol
      if (msg.jsonrpc === '2.0') {
        if (msg.method === 'ui/initialize') {
          window.parent.postMessage({
            jsonrpc: '2.0', id: msg.id,
            result: { protocolVersion: '0.1.0', capabilities: {} }
          }, '*');
        } else if (msg.method === 'ui/toolResult') {
          handleToolResult(msg.params);
        }
      }

      // Simple data push (REST delivery via frontend)
      if (msg.type === 'toolResult') {
        handleToolResult(msg.data);
      }
    });

    // Signal readiness to host
    window.parent.postMessage({
      jsonrpc: '2.0', method: 'ui/ready', params: {}
    }, '*');
  </script>
</body>
</html>
```

### postMessage Protocol

Apps communicate with the host via `window.postMessage` using JSON-RPC 2.0:

| Direction | Method | Description |
|-----------|--------|-------------|
| App -> Host | `ui/ready` | App signals it is ready to receive data |
| Host -> App | `ui/initialize` | Host initializes the app (MCP transport) |
| App -> Host | Response to `ui/initialize` | App confirms with `protocolVersion` |
| Host -> App | `ui/toolResult` | Host sends tool result data |
| App -> Host | `resize` | App requests iframe height change (optional) |

The frontend also sends a simple `{type: 'toolResult', data: ...}` message on iframe load for REST-based delivery. Apps should handle both protocols.

### App Guidelines

- **Self-contained**: Each HTML file must be fully standalone (inline styles, CDN scripts)
- **Three states**: Always handle loading, result, and error states
- **Tailwind CSS**: Use the CDN build for styling (`<script src="https://cdn.tailwindcss.com"></script>`)
- **Sandboxed**: Apps run inside `<iframe sandbox="allow-scripts">` with no access to the parent DOM
- **Max height**: The iframe caps at 600px; use the `resize` message to request more space

### Backend Proxy

The backend proxies app requests to the toolset with API key authentication:

| Method | Backend Endpoint | Toolset Endpoint | Description |
|--------|------------------|------------------|-------------|
| GET | `/api/tools/apps` | `/apps` | List available apps |
| GET | `/api/tools/apps/{tool_name}` | `/apps/{tool_name}` | Get app HTML |

The frontend always fetches through the backend proxy so that service-to-service authentication is handled transparently.

### Existing Apps

| Category | Tools with Apps |
|----------|----------------|
| `calculator` | add, subtract, multiply, divide, exponentiate, factorial, is_prime, square_root, absolute_value, logarithm, modulo, greatest_common_divisor |
| `search` | tavily_web_search |
| `database` | execute_query, list_tables, describe_table |
| `data` | read_csv_file, query_csv_file |
| `files` | convert_pdf_to_markdown, markdown_to_table |
| `local` | execute_shell_command |
| `image` | extract_text_from_image |
| `storage` | list_buckets, list_objects, get_object_metadata, get_presigned_url |

If no app exists for a tool, results display as formatted JSON.

## Skills

Skills provide metadata about tool categories for AI assistants. Create a `SKILL.md` file in your tool category folder:

```markdown
---
name: managing-local-system
description: Manages local filesystem operations and runs shell commands. Use when working with local files or executing commands.
---

# Local System Tools

## File Operations

\`\`\`python
result = await filesystem_write_file(content="Hello", filename="test.txt")
\`\`\`
```

### Skill Best Practices

Follow the [Claude Code Skill Best Practices](https://docs.anthropic.com/en/docs/claude-code/skills#best-practices):

1. **Naming**: Use gerund phrases (e.g., `managing-local-system`, `processing-data`)
2. **Description**: Write in third person, describe what the skill does and when to use it
3. **Content**: Include code examples, parameter tables, and usage guidance
4. **Progressive Disclosure**: Start with common operations, then advanced options

## Tool Configuration

Control which tools are exposed via `config/tools.yaml`. Empty config loads all tools.

```yaml
# Include specific categories/tools
include:
  categories:
    - local
    - data
  tools:
    - tavily_web_search

# Exclude categories/tools (supports wildcards)
exclude:
  tools:
    - shell_*
```

**Rules:**
1. Empty config = load ALL tools
2. `include` filters to only specified categories/tools
3. `exclude` removes from the result (supports `*`, `?` wildcards)

---

# API Reference

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Server info |
| GET | `/docs` | Swagger UI |
| GET | `/tools` | List all tools with skill metadata |
| GET | `/tools/{category}` | Category details with full skill content |
| GET | `/tools/{category}/{tool_name}` | Tool details and input schema |
| POST | `/tools/{tool_name}` | Execute a tool |
| GET | `/apps` | List available MCP App bundles |
| GET | `/apps/{tool_name}` | Get MCP App HTML for a tool |
| - | `/mcp` | MCP server (SSE transport) |

## Example

```bash
curl -X POST http://localhost:8003/tools/local_greet \
  -H "Content-Type: application/json" \
  -d '{"name": "World"}'
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PORT` | Server port (default `8003`) |
| `MCP_SERVER_URL` | Display URL for MCP server |
| `SERVICE_API_KEY` | API key for service-to-service auth (must match backend) |
| `JWT_SECRET_KEY` | JWT signing key for per-user auth (must match backend). Unset = dev mode (no auth) |
| `TOOLSET_REQUIRE_AUTH` | Set `true` to enforce auth (401 if no user context). Default `false` |
| `DATABASE_URL` | PostgreSQL connection string (required for permission checks against `iam.relationships`) |
| `TAVILY_API_KEY` | Tavily web search API key |
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth Client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth Client Secret |

---

# Available Tools

> Tools are auto-discovered from `src/tools/`. This list may change.

| Category | Tools | Description |
|----------|-------|-------------|
| `local` | Calculator, Shell, File System | Local system operations |
| `data` | CSV, Pandas | Data processing |
| `database` | PostgreSQL | Database queries and schema inspection |
| `files` | PDF to Markdown, Markdown Tables | File conversion and extraction |
| `image` | OCR (Tesseract) | Image text extraction |
| `search` | Tavily | Web search |
| `storage` | MinIO | S3-compatible object storage |
| `google` | Gmail, Calendar, Drive, Docs, Sheets, Slides, Forms, Tasks, Chat | Google Workspace |

> **[Google Workspace Setup Guide →](src/tools/google/README.md)**

---

# Development

## Running Tests

```bash
# From monorepo root
make test-toolset

# Or from toolset directory
uv run pytest tests/ -v

# Run specific test
uv run pytest tests/humcp/test_config.py -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html
```

## Linting and Formatting

```bash
# From monorepo root
make lint
make format

# Or directly
uv run ruff check .
uv run ruff format .
```

## Pre-commit Hooks

```bash
uv run pre-commit run --all-files
```

## Project Layout

```
.
├── config/tools.yaml           # Tool filtering config
├── src/
│   ├── humcp/                  # Core library
│   │   ├── decorator.py        # @tool decorator
│   │   ├── config.py           # Config loader
│   │   ├── routes.py           # REST routes
│   │   └── server.py           # create_app()
│   ├── apps/                   # MCP App HTML bundles
│   │   └── <category>/
│   │       └── <tool_name>.html
│   ├── tools/                  # Tool implementations
│   │   └── <category>/
│   │       ├── SKILL.md        # Category skill metadata
│   │       └── *.py            # Tool files
│   └── main.py
└── tests/
```

## License

MIT License
