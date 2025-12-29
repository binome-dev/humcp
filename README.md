# HuMCP

HuMCP is a simple server that exposes tools via both MCP (Model Context Protocol) and REST endpoints with auto-generated Swagger documentation.

## Features

- Simple `@tool` decorator to register tools
- Auto-generated REST endpoints at `/tools/*`
- MCP server at `/mcp` for AI assistant integration
- Auto-generated Swagger/OpenAPI documentation at `/docs`
- Tools organized by category with info endpoints
- Docker Compose setup for easy deployment

## Prerequisites

- Python >= 3.13
- [uv](https://github.com/astral-sh/uv) (recommended)
- Docker & Docker Compose (optional)

## Project Layout

```
.
├── docker/
│   └── Dockerfile
├── src/
│   ├── humcp/                  # Core library
│   │   ├── registry.py         # Tool registry
│   │   ├── decorator.py        # @tool decorator
│   │   ├── routes.py           # REST route generation
│   │   └── server.py           # create_app() function
│   ├── tools/                  # Your tools go here
│   │   ├── local/              # Local utility tools
│   │   ├── data/               # Data manipulation tools
│   │   └── ...
│   └── main.py                 # App entry point
├── tests/
├── docker-compose.yml
└── pyproject.toml
```

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

## Adding New Tools

1. Create a `.py` file in `src/tools/<category>/` (e.g., `src/tools/local/my_tool.py`)
2. Use the `@tool` decorator:

```python
from src.humcp import tool

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

### Documentation is Critical! 🚨

**Your docstring is not just a comment - it becomes the tool's user interface:**

- **REST API**: Appears in Swagger/OpenAPI docs at `/docs`
- **MCP Protocol**: Sent to AI assistants to help them understand when and how to use your tool
- **Type hints**: Combined with docstrings to generate input schemas

**Best Practices:**

✅ **DO:**
- Write clear, concise docstrings that explain what the tool does
- Document all parameters with their purpose and expected format
- Describe what the tool returns
- Include examples for complex tools
- Use proper Python type hints

❌ **DON'T:**
- Leave tools without docstrings
- Use vague descriptions like "does stuff" or "helper function"
- Forget to document parameters or return values

**Example of Good Documentation:**

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

    Example:
        {"pattern": "*.json", "directory": "/app/config"}
    """
    ...
```

### Tool Naming

The `@tool` decorator supports flexible naming:

```python
# Auto-generated name: "{category}_{function_name}"
# Category from parent folder, e.g., "local_greet"
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

### Tool Response Pattern

Tools should return a dictionary:

```python
# Success
return {"success": True, "data": {"result": value}}

# Error
return {"success": False, "error": "Error message"}
```

## API Endpoints

### Info Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Server info |
| GET | `/tools` | List all tools grouped by category |
| GET | `/tools/{category}` | List tools in a category |
| GET | `/tools/{category}/{tool_name}` | Get tool details and input schema |

### Tool Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tools/{tool_name}` | Execute a tool |

Example:
```bash
curl -X POST http://localhost:8080/tools/local_greet \
  -H "Content-Type: application/json" \
  -d '{"name": "World"}'
```

### MCP Endpoint

| Endpoint | Description |
|----------|-------------|
| `/mcp` | MCP server (SSE transport) |

## Docker Usage

```bash
docker compose up --build
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PORT` | Server port (default `8080`) |
| `MCP_SERVER_URL` | Display URL for MCP server |
| `TAVILY_API_KEY` | API key for Tavily search tools |

## Development

**Run tests:**
```bash
uv run pytest
```

**Run linter:**
```bash
uv run pre-commit run --all-file
```

## License

MIT License
