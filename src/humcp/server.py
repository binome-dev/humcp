"""HuMCP Server - app creation with REST and MCP endpoints."""

import importlib.util
import inspect
import logging
import sys
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path
from types import ModuleType
from typing import Any, get_type_hints

from dotenv import load_dotenv
from fastapi import FastAPI
from fastmcp import FastMCP
from pydantic import TypeAdapter

from src.humcp.auth import create_auth_provider
from src.humcp.config import DEFAULT_CONFIG_PATH, filter_tools, load_config
from src.humcp.decorator import (
    RegisteredTool,
    ToolInfo,
    get_tool_category,
    get_tool_name,
    is_tool,
)
from src.humcp.routes import build_openapi_tags, register_routes

load_dotenv()

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


def _build_parameters_schema(func: Callable[..., Any]) -> dict[str, Any]:
    """Build JSON Schema for a function's parameters using pydantic."""
    sig = inspect.signature(func)
    hints = get_type_hints(func)

    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue
        annotation = hints.get(name, Any)
        try:
            adapter = TypeAdapter(annotation)
            prop_schema = adapter.json_schema()
        except Exception:
            prop_schema = {}

        # Add description from default if it's a pydantic Field, otherwise skip
        properties[name] = prop_schema

        if param.default is inspect.Parameter.empty:
            required.append(name)
        elif param.default is not inspect.Parameter.empty and param.default is not None:
            properties[name]["default"] = param.default

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required

    return schema


def _discover_and_register(
    mcp: FastMCP, modules: list[ModuleType]
) -> list[RegisteredTool]:
    """Discover @tool functions and register with FastMCP.

    Returns list of RegisteredTool (ToolInfo + category).
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

            # Register with FastMCP (v3 returns the original function, not FunctionTool)
            mcp.tool(name=tool_name)(func)

            # Build ToolInfo ourselves
            tool_info = ToolInfo(
                name=tool_name,
                description=func.__doc__ or "",
                parameters=_build_parameters_schema(func),
                fn=func,
            )
            tools.append(RegisteredTool(tool=tool_info, category=category))
            logger.debug("Registered: %s (category: %s)", tool_name, category)

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

    # Create auth provider (respects AUTH_ENABLED env var)
    auth_provider = create_auth_provider()

    # Create MCP server
    mcp = FastMCP("HuMCP Server", auth=auth_provider)

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

    # Register all REST routes (tools, auth, info endpoints)
    register_routes(
        app,
        tools_path=path,
        tools=filtered,
        auth_provider=auth_provider,
        title=title,
        version=version,
    )
    logger.info("Registered %d REST endpoints", len(filtered))

    # Mount OAuth routes at root level
    # This includes: /.well-known/*, /authorize, /token, /register, /auth/callback, /consent
    if auth_provider:
        oauth_routes = auth_provider.get_routes(mcp_path="/mcp")
        for route in oauth_routes:
            app.routes.append(route)
        logger.info("Mounted %d OAuth routes at root level", len(oauth_routes))

    app.mount("/mcp", mcp_http_app)
    return app
