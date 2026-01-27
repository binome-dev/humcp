# HuMCP

HuMCP is a simple server that exposes tools via both MCP (Model Context Protocol) and REST endpoints with auto-generated Swagger documentation.

## Features

- Simple `@tool` decorator to register tools
- Auto-generated REST endpoints at `/tools/*`
- MCP server at `/mcp` for AI assistant integration
- Auto-generated Swagger/OpenAPI documentation at `/docs`
- Tools organized by category with skill metadata
- Configurable tool filtering via YAML config
- Docker Compose setup for easy deployment

## Quick Start

```bash
# Install dependencies
uv sync

# Copy environment file
cp .env.example .env

# Run server
uv run uvicorn src.main:app --host 0.0.0.0 --port 8080
```

- REST API & Swagger UI: [http://localhost:8080/docs](http://localhost:8080/docs)
- MCP endpoint: `http://localhost:8080/mcp`

### Docker

```bash
docker compose up --build
```

## Prerequisites

- Python >= 3.13
- [uv](https://github.com/astral-sh/uv) (recommended)
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
| - | `/mcp` | MCP server (SSE transport) |

## Example

```bash
curl -X POST http://localhost:8080/tools/local_greet \
  -H "Content-Type: application/json" \
  -d '{"name": "World"}'
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PORT` | Server port (default `8080`) |
| `MCP_SERVER_URL` | Display URL for MCP server |
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
| `files` | PDF to Markdown | File conversion |
| `search` | Tavily | Web search |
| `google` | Gmail, Calendar, Drive, Docs, Sheets, Slides, Forms, Tasks, Chat | Google Workspace |

> **[Google Workspace Setup Guide →](src/tools/google/README.md)**

---

# Development

```bash
# Run tests
uv run pytest

# Run linter
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
│   ├── tools/                  # Tool implementations
│   │   └── <category>/
│   │       ├── SKILL.md        # Category skill metadata
│   │       └── *.py            # Tool files
│   └── main.py
└── tests/
```

## License

MIT License
