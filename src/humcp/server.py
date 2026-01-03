"""HuMCP Server - app creation with REST and MCP endpoints."""

import importlib.util
import inspect
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import ModuleType

from fastapi import FastAPI
from fastmcp import FastMCP

from src.humcp.config import DEFAULT_CONFIG_PATH, filter_tools, load_config
from src.humcp.decorator import (
    RegisteredTool,
    get_tool_category,
    get_tool_name,
    is_tool,
)
from src.humcp.routes import build_openapi_tags, register_routes

logger = logging.getLogger("humcp")


def _load_modules(tools_path: Path) -> list[ModuleType]:
    """Load Python modules from a directory."""
    if not tools_path.exists():
        return []

    modules: list[ModuleType] = []
    for file_path in sorted(tools_path.rglob("*.py")):
        if file_path.name.startswith("_"):
            continue

        relative = file_path.relative_to(tools_path)
        module_name = (
            f"humcp_tools.{relative.with_suffix('').as_posix().replace('/', '.')}"
        )

        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                modules.append(module)
                logger.debug("Loaded module: %s", module_name)
        except Exception as e:
            logger.warning("Error loading %s: %s", file_path.name, e)

    return modules


def _discover_and_register(
    mcp: FastMCP, modules: list[ModuleType]
) -> list[RegisteredTool]:
    """Discover @tool functions and register with FastMCP.

    Returns list of RegisteredTool (FunctionTool + category).
    """
    tools: list[RegisteredTool] = []
    seen_names: set[str] = set()

    for module in modules:
        for _, func in inspect.getmembers(module, inspect.isfunction):
            if not is_tool(func):
                continue

            # Get tool metadata from decorator
            tool_name = get_tool_name(func)
            category = get_tool_category(func)

            # Check for duplicates
            if tool_name in seen_names:
                logger.warning("Duplicate tool '%s', skipping", tool_name)
                continue

            seen_names.add(tool_name)

            # Register with FastMCP using custom name - returns FunctionTool
            fn_tool = mcp.tool(name=tool_name)(func)
            tools.append(RegisteredTool(tool=fn_tool, category=category))
            logger.debug("Registered: %s (category: %s)", fn_tool.name, category)

    return tools


def create_app(
    tools_path: Path | str | None = None,
    config_path: Path | str | None = None,
    title: str = "HuMCP Server",
    description: str = "REST and MCP endpoints for tools",
    version: str = "1.0.0",
) -> FastAPI:
    """Create FastAPI app with REST (/tools) and MCP (/mcp) endpoints."""
    path = Path(tools_path) if tools_path else Path(__file__).parent.parent / "tools"

    # Create MCP server
    mcp = FastMCP("HuMCP Server")

    # Load modules and register tools with FastMCP
    modules = _load_modules(path)
    tools = _discover_and_register(mcp, modules)
    logger.info("Registered %d tools from %s", len(tools), path)

    # Filter tools by config
    cfg_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    config = load_config(cfg_path)
    filtered = filter_tools(config, tools, validate=True)
    logger.info("Filtered: %d/%d tools", len(filtered), len(tools))

    # Setup MCP HTTP app
    mcp_http_app = mcp.http_app(path="/")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        async with mcp_http_app.router.lifespan_context(mcp_http_app):
            yield

    # Create FastAPI app
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        lifespan=lifespan,
        openapi_tags=build_openapi_tags(filtered),
    )

    # Register REST routes
    register_routes(app, tools_path=path, tools=filtered)

    # Root endpoint
    mcp_url = os.getenv("MCP_SERVER_URL", "http://0.0.0.0:8080/mcp")

    @app.get("/", tags=["Info"])
    async def root():
        return {
            "name": title,
            "version": version,
            "mcp_server": mcp_url,
            "tools_count": len(filtered),
            "endpoints": {"docs": "/docs", "tools": "/tools", "mcp": "/mcp"},
        }

    app.mount("/mcp", mcp_http_app)
    return app
