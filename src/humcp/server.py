"""HuMCP Server - app creation with REST and MCP endpoints."""

import importlib.util
import inspect
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import ModuleType

from dotenv import load_dotenv
from fastapi import FastAPI
from fastmcp import FastMCP

from src.humcp.auth import create_auth_provider
from src.humcp.registry import TOOL_REGISTRY
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

    # Create auth provider (respects AUTH_ENABLED env var)
    auth_provider = create_auth_provider()

    # Create MCP server
    mcp = FastMCP("HuMCP Server", auth=auth_provider)
    seen: set[Callable[..., Any]] = set()
    for reg in TOOL_REGISTRY:
        if reg.func not in seen:
            seen.add(reg.func)
            mcp.tool(name=reg.name)(reg.func)
            logger.info("Registered MCP tool: %s", reg.name)

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
        auth_provider=auth_provider,
        tools_path=path,
        title=title,
        version=version,
    )
    logger.info("Registered %d REST endpoints", len(TOOL_REGISTRY))

    # Mount OAuth routes at root level
    # This includes: /.well-known/*, /authorize, /token, /register, /auth/callback, /consent
    if auth_provider:
        oauth_routes = auth_provider.get_routes(mcp_path="/mcp")
        for route in oauth_routes:
            app.routes.append(route)
        logger.info("Mounted %d OAuth routes at root level", len(oauth_routes))

    app.mount("/mcp", mcp_http_app)
    return app
