"""HuMCP Server - app creation with REST and MCP endpoints."""

import importlib.util
import logging
import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.client import Client
from mcp.types import Tool

from .decorator import TOOL_REGISTRY
from .routes import register_routes

logger = logging.getLogger("humcp")

DEFAULT_TOOLS_PATH = Path(__file__).parent.parent / "tools"


def _discover_tools(tools_path: Path) -> None:
    """Scan and import all tool modules to trigger @tool registration."""
    if not tools_path.exists():
        logger.warning("Tools path not found: %s", tools_path)
        return

    for py_file in tools_path.rglob("*.py"):
        if py_file.name.startswith("_"):
            continue

        module_name = f"tools.{py_file.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.debug("Loaded tool module: %s", py_file.name)
        except Exception as e:
            logger.warning("Failed to load %s: %s", py_file.name, e)


def create_app(
    tools_path: Path | None = None,
    title: str = "HuMCP Server",
    description: str = "REST and MCP endpoints for tools",
    version: str = "1.0.0",
) -> FastAPI:
    """Create FastAPI app with REST (/tools) and MCP (/mcp) endpoints.

    Args:
        tools_path: Path to tools directory. Defaults to src/tools/.
        title: App title for OpenAPI docs.
        description: App description.
        version: App version.

    Returns:
        FastAPI app with:
        - REST endpoints at /tools/{tool_name}
        - MCP server at /mcp
        - Info endpoints at /, /tools, /tools/{category}
    """
    # Auto-discover and import tool modules
    _discover_tools(tools_path or DEFAULT_TOOLS_PATH)

    # Create MCP server with all registered tools
    mcp = FastMCP("HuMCP Server")
    seen: set[Callable[..., Any]] = set()
    for reg in TOOL_REGISTRY:
        if reg.func not in seen:
            seen.add(reg.func)
            mcp.tool(name=reg.name)(reg.func)
            logger.info("Registered tool: %s", reg.name)

    mcp_http_app = mcp.http_app(path="/")
    mcp_client = Client(mcp)
    tools_state: dict[str, Tool] = {}

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        async with mcp_http_app.router.lifespan_context(mcp_http_app):
            await mcp_client.__aenter__()
            for t in await mcp_client.list_tools():
                tools_state[t.name] = t
            logger.info("Loaded %d tools", len(tools_state))
            register_routes(_app, mcp_client, tools_state)
            yield
            await mcp_client.__aexit__(None, None, None)

    app = FastAPI(
        title=title,
        description=description,
        version=version,
        lifespan=lifespan,
    )

    # Root info endpoint
    mcp_url = os.getenv("MCP_SERVER_URL", "http://0.0.0.0:8080/mcp")

    @app.get("/", tags=["Info"])
    async def root():
        return {
            "name": title,
            "version": version,
            "mcp_server": mcp_url,
            "tools_count": len(tools_state),
            "endpoints": {"docs": "/docs", "tools": "/tools", "mcp": "/mcp"},
        }

    # Mount MCP
    app.mount("/mcp", mcp_http_app)

    return app
