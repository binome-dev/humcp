"""HuMCP Server - app creation with REST and MCP endpoints."""

import importlib.util
import logging
import os
import sys
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastmcp import FastMCP

from src.humcp.registry import TOOL_REGISTRY
from src.humcp.routes import register_routes

logger = logging.getLogger("humcp")


def _discover_tools(tools_path: Path) -> int:
    """Auto-discover and import tool modules from a directory.

    Recursively scans the directory for Python files (excluding those starting
    with '_') and imports them, triggering any @tool decorators.

    Args:
        tools_path: Directory to scan for tool modules.

    Returns:
        Number of modules successfully loaded.
    """
    if not tools_path.exists():
        logger.debug("Tools path does not exist: %s", tools_path)
        return 0

    loaded = 0
    for file_path in sorted(tools_path.rglob("*.py")):
        if file_path.name.startswith("_"):
            continue

        # Create unique module name based on relative path
        # e.g., tools/local/calculator.py -> humcp_tools.local.calculator
        relative = file_path.relative_to(tools_path)
        module_name = (
            f"humcp_tools.{relative.with_suffix('').as_posix().replace('/', '.')}"
        )

        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.warning("Could not create spec for %s", file_path)
                continue

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            loaded += 1
            logger.debug("Loaded tool module: %s", module_name)
        except Exception as e:
            logger.warning("Failed to load %s: %s", file_path.name, e)

    return loaded


def create_app(
    tools_path: Path | str | None = None,
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
        FastAPI app with REST at /tools/* and MCP at /mcp
    """
    # Auto-discover tool modules
    path = Path(tools_path) if tools_path else Path(__file__).parent.parent / "tools"
    loaded = _discover_tools(path)
    logger.info("Discovered %d tool modules from %s", loaded, path)

    # Create MCP server
    mcp = FastMCP("HuMCP Server")
    seen: set[Callable[..., Any]] = set()
    for reg in TOOL_REGISTRY:
        if reg.func not in seen:
            seen.add(reg.func)
            mcp.tool(name=reg.name)(reg.func)
            logger.info("Registered MCP tool: %s", reg.name)

    mcp_http_app = mcp.http_app(path="/")

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        async with mcp_http_app.router.lifespan_context(mcp_http_app):
            yield

    app = FastAPI(
        title=title,
        description=description,
        version=version,
        lifespan=lifespan,
    )

    # Register REST routes from TOOL_REGISTRY
    register_routes(app)
    logger.info("Registered %d REST endpoints", len(TOOL_REGISTRY))

    # Root info endpoint
    mcp_url = os.getenv("MCP_SERVER_URL", "http://0.0.0.0:8080/mcp")

    @app.get("/", tags=["Info"])
    async def root():
        return {
            "name": title,
            "version": version,
            "mcp_server": mcp_url,
            "tools_count": len(TOOL_REGISTRY),
            "endpoints": {"docs": "/docs", "tools": "/tools", "mcp": "/mcp"},
        }

    # Mount MCP
    app.mount("/mcp", mcp_http_app)
    return app
