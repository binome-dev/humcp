# HuMCP

HuMCP is a [FastMCP](https://github.com/modelcontextprotocol/fastmcp) server with a FastAPI adapter that exposes MCP tools as REST endpoints with auto-generated Swagger documentation. It provides a curated set of local utility and data manipulation tools.

## Services

- **humcp-server** – FastMCP server exposing tools via SSE transport
- **humcp-fastapi-server** – FastAPI adapter that auto-generates REST endpoints for all MCP tools

## Features

- Built-in MCP Tools
- Auto-generated Swagger/OpenAPI documentation at `/docs`
- Tools organized by category with info endpoints (`/tools`, `/tools/{category}`)
- Docker Compose setup for easy deployment

## Prerequisites

- Python ≥ 3.13
- [uv](https://github.com/astral-sh/uv) (recommended)
- Docker & Docker Compose (optional)

## Project Layout

```
.
├── docker/
│   ├── Dockerfile.mcp           # MCP server container
│   └── Dockerfile.fastapi       # FastAPI adapter container
├── src/
│   ├── server.py                # FastMCP server entry point
│   ├── main.py                  # FastAPI app entry point
│   ├── adapter/
│   │   ├── adapter.py           # FastMCPFastAPIAdapter class
│   │   ├── routes.py            # Route generation from MCP tools
│   │   └── models.py            # Pydantic model generation
│   └── tools/                   # MCP Tools
│
├── tests/                       # Test suite
├── docker-compose.yml
└── pyproject.toml
```

## Local Setup

```bash
uv sync
cp .env.example .env
```

## Running Locally

```bash
UV_CACHE_DIR=.uv-cache uv run uvicorn src.main:app --host 0.0.0.0 --port 8080
```

- MCP endpoint (same port): `http://localhost:8080/mcp`
- Swagger UI: [http://localhost:8080/docs](http://localhost:8080/docs)

## Docker Usage

```bash
docker compose up --build
```

- MCP endpoint: `http://localhost:8080/mcp`
- Swagger UI: [http://localhost:8080/docs](http://localhost:8080/docs)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PORT` | Port to run the combined FastAPI + MCP server (default `8080`) |
| `MCP_PORT` | Legacy override for MCP port if `PORT` is not set |
| `MCP_SERVER_URL` | Optional display URL for the MCP server (defaults to `http://0.0.0.0:<PORT>/mcp`) |
| `TAVILY_API_KEY` | API key for Tavily web search tools |

## Available Tools

- Calculator (`calculator/`)
- File System (`filesystem/`)
- Shell (`shell/`)
- CSV (`csv/`)
- Pandas (`pandas/`)
- Search (`search/`)

## Development

**Add new tools:**
1. Create tool file in `src/tools/<category>/`
2. Implement `register_tools(mcp: FastMCP)` function
3. Import and register in `src/server.py`

**Run tests:**
```bash
uv run pytest
```

**Run linter:**
```bash
uv run ruff check
```

## License

MIT License
