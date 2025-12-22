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
uv run uvicorn src.main:app --host 0.0.0.0 --port 8080
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
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth 2.0 Client ID for Google Workspace tools |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth 2.0 Client Secret |

## Available Tools

### Local Tools
- Calculator (`calculator/`)
- File System (`filesystem/`)
- Shell (`shell/`)
- CSV (`csv/`)
- Pandas (`pandas/`)
- Search (`search/`)

### Google Workspace Tools
- Gmail (`gmail/`) - Search, read, send emails
- Calendar (`calendar/`) - List, create, delete events
- Drive (`drive/`) - List, search, read files
- Tasks (`tasks/`) - Manage task lists and tasks
- Docs (`docs/`) - Search, create, edit documents
- Sheets (`sheets/`) - Read, write, create spreadsheets
- Slides (`slides/`) - Create and manage presentations
- Forms (`forms/`) - Create forms, read responses
- Chat (`chat/`) - List spaces, send messages

## Google Workspace Setup

To use the Google Workspace tools, you need to set up OAuth 2.0 credentials:

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **Select a project** → **New Project**
3. Enter a project name (e.g., "HuMCP") and click **Create**

### 2. Enable Required APIs

Navigate to **APIs & Services** → **Library** and enable the APIs you need:

- Gmail API
- Google Calendar API
- Google Drive API
- Google Tasks API
- Google Docs API
- Google Sheets API
- Google Slides API
- Google Forms API
- Google Chat API

### 3. Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** (or **Internal** if using Google Workspace)
3. Fill in the required fields:
   - App name: "HuMCP"
   - User support email: your email
   - Developer contact: your email
4. Click **Save and Continue**
5. Skip scopes (they're requested programmatically)
6. **Add test users**: Add your Google account email
7. Click **Save and Continue**

### 4. Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select application type:
   - **Desktop app** (recommended for local development)
   - Or **Web application** (add `http://localhost` to redirect URIs)
4. Enter a name (e.g., "HuMCP Desktop Client")
5. Click **Create**
6. Copy the **Client ID** and **Client Secret**

### 5. Configure Environment

Add to your `.env` file:

```bash
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-your-client-secret
```

### 6. First-Time Authentication

When you first call any Google tool:
1. A browser window opens for Google login
2. Sign in with a test user account
3. Grant the requested permissions
4. Tokens are saved to `~/.humcp/google_token.json`

Subsequent calls use the cached token (auto-refreshes when expired).

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
