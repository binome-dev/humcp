"""HuMCP Server - app creation with REST and MCP endpoints."""

import importlib.util
import inspect
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import ModuleType

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastmcp import FastMCP
from fastmcp.server.apps import AppConfig
from fastmcp.server.auth.providers.jwt import JWTVerifier

from src.humcp.auth import create_auth_provider
from src.humcp.config import DEFAULT_CONFIG_PATH, filter_tools, load_config
from src.humcp.decorator import (
    RegisteredTool,
    get_tool_app,
    get_tool_category,
    get_tool_name,
    is_tool,
)
from src.humcp.middleware import APIKeyMiddleware
from src.humcp.playground import get_playground_html
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


def _discover_apps(apps_path: Path) -> dict[str, Path]:
    """Discover MCP App HTML bundles in the apps directory.

    Returns mapping of tool_name -> html_file_path.
    Convention: apps/{category}/{tool_name}.html
    """
    if not apps_path.exists():
        return {}

    app_map: dict[str, Path] = {}
    for html_file in sorted(apps_path.rglob("*.html")):
        tool_name = html_file.stem
        app_map[tool_name] = html_file
        logger.debug("Discovered app: %s -> %s", tool_name, html_file)

    return app_map


def _make_app_resource_fn(path: Path):
    """Create a named function for serving an app HTML file as MCP resource."""

    async def read_app_html() -> str:
        return path.read_text(encoding="utf-8")

    read_app_html.__name__ = f"app_{path.stem}"
    read_app_html.__qualname__ = f"app_{path.stem}"
    return read_app_html


def _register_app_resources(
    mcp: FastMCP, apps_path: Path, app_map: dict[str, Path]
) -> None:
    """Register ui:// MCP resources for discovered app HTML bundles."""
    for tool_name, html_file in app_map.items():
        relative = html_file.relative_to(apps_path)
        uri = f"ui://{relative.as_posix()}"
        reader_fn = _make_app_resource_fn(html_file)
        mcp.resource(uri, name=f"app_{tool_name}")(reader_fn)
        logger.debug("Registered ui:// resource: %s", uri)


def _discover_and_register(
    mcp: FastMCP,
    modules: list[ModuleType],
    app_map: dict[str, Path] | None = None,
    apps_path: Path | None = None,
) -> list[RegisteredTool]:
    """Discover @tool functions and register with FastMCP.

    If app_map is provided, tools with matching HTML apps get AppConfig attached
    for MCP Apps support.

    Returns list of RegisteredTool (FunctionTool + category).
    """
    app_map = app_map or {}
    tools: list[RegisteredTool] = []
    seen_names: set[str] = set()

    for module in modules:
        for _, func in inspect.getmembers(module, inspect.isfunction):
            if not is_tool(func):
                continue

            # Get tool metadata from decorator
            tool_name = get_tool_name(func)
            category = get_tool_category(func)
            app = get_tool_app(func)

            # Check for duplicates
            if tool_name in seen_names:
                logger.warning("Duplicate tool '%s', skipping", tool_name)
                continue

            seen_names.add(tool_name)

            # Build app config if matching HTML app exists
            app_config = None
            if tool_name in app_map and apps_path:
                relative = app_map[tool_name].relative_to(apps_path)
                resource_uri = f"ui://{relative.as_posix()}"
                app_config = AppConfig(resource_uri=resource_uri)
                logger.debug("Attached app to tool '%s': %s", tool_name, resource_uri)

            # Register with FastMCP (v3 returns the original function, not FunctionTool)
            mcp.tool(name=tool_name, app=app_config)(func)

            # Access the FunctionTool synchronously from FastMCP's internal registry
            fn_tool = mcp._local_provider._components[f"tool:{tool_name}@"]
            tools.append(RegisteredTool(tool=fn_tool, category=category, app=app))
            logger.debug("Registered: %s (category: %s)", fn_tool.name, category)

    return tools


def create_app(
    tools_path: Path | str | None = None,
    config_path: Path | str | None = None,
    apps_path: Path | str | None = None,
    title: str = "HuMCP Server",
    description: str = "REST and MCP endpoints for tools",
    version: str = "1.0.0",
) -> FastAPI:
    """Create FastAPI app with REST (/tools), MCP (/mcp), and Apps (/apps) endpoints."""
    path = Path(tools_path) if tools_path else Path(__file__).parent.parent / "tools"
    a_path = Path(apps_path) if apps_path else Path(__file__).parent.parent / "apps"

    # Select MCP auth provider:
    # - JWT_SECRET_KEY set → JWTVerifier (graphite/service-to-service mode)
    # - GOOGLE_OAUTH_CLIENT_ID + AUTH_ENABLED=true → GoogleProvider (standalone mode)
    # - Neither → no MCP auth (dev mode)
    jwt_secret = os.getenv("JWT_SECRET_KEY", "")
    if jwt_secret:
        mcp_auth = JWTVerifier(public_key=jwt_secret, algorithm="HS256")
        mcp = FastMCP("HuMCP Server", auth=mcp_auth)
        auth_provider = None  # Google OAuth not used when JWT mode is active
        logger.info("Using JWT auth for MCP (JWT_SECRET_KEY set)")
    else:
        # Fall back to Google OAuth (or None if not configured)
        auth_provider = create_auth_provider()
        mcp = FastMCP("HuMCP Server", auth=auth_provider)
        if auth_provider:
            logger.info("Using Google OAuth for MCP")

    # Discover MCP App HTML bundles
    app_map = _discover_apps(a_path)
    if app_map:
        logger.info("Discovered %d MCP App bundles from %s", len(app_map), a_path)
        _register_app_resources(mcp, a_path, app_map)

    # Load modules and register tools with FastMCP
    modules = _load_modules(path)
    tools = _discover_and_register(mcp, modules, app_map=app_map, apps_path=a_path)
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

    # Add API key authentication middleware
    app.add_middleware(APIKeyMiddleware)

    # Register REST routes (tools, auth, info endpoints)
    register_routes(
        app,
        tools_path=path,
        tools=filtered,
        auth_provider=auth_provider,
        title=title,
        version=version,
        apps_count=len(app_map),
    )
    logger.info("Registered %d REST endpoints", len(filtered))

    # Mount OAuth routes at root level (Google OAuth mode only)
    if auth_provider:
        oauth_routes = auth_provider.get_routes(mcp_path="/mcp")
        for route in oauth_routes:
            app.routes.append(route)
        logger.info("Mounted %d OAuth routes at root level", len(oauth_routes))

    # Apps REST delivery endpoint
    @app.get("/apps/{tool_name}", tags=["Apps"], response_class=HTMLResponse)
    async def get_app_html(tool_name: str) -> HTMLResponse:
        """Serve MCP App HTML bundle for a tool (REST delivery)."""
        html_file = app_map.get(tool_name)
        if not html_file or not html_file.exists():
            return HTMLResponse(status_code=404, content="App not found")
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))

    @app.get("/apps", tags=["Apps"])
    async def list_apps() -> dict:
        """List available MCP App bundles."""
        return {
            "total_apps": len(app_map),
            "apps": [
                {
                    "tool_name": name,
                    "rest_endpoint": f"/apps/{name}",
                    "mcp_resource": f"ui://{p.relative_to(a_path).as_posix()}",
                }
                for name, p in sorted(app_map.items())
            ],
        }

    # Playground endpoint
    @app.get("/playground", tags=["Info"], response_class=HTMLResponse)
    async def playground():
        """Interactive tool browser and executor."""
        return HTMLResponse(content=get_playground_html())

    # Root info endpoint
    mcp_url = os.getenv("MCP_SERVER_URL", "http://0.0.0.0:8080/mcp")
    auth_enabled = auth_provider is not None

    @app.get("/", tags=["Info"])
    async def root():
        """Server information endpoint."""
        endpoints: dict[str, str] = {
            "docs": "/docs",
            "playground": "/playground",
            "tools": "/tools",
            "apps": "/apps",
            "mcp": "/mcp",
        }
        if auth_enabled:
            endpoints["login"] = "/login"
        return {
            "name": title,
            "version": version,
            "mcp_server": mcp_url,
            "tools_count": len(filtered),
            "apps_count": len(app_map),
            "auth_enabled": auth_enabled,
            "endpoints": endpoints,
        }

    app.mount("/mcp", mcp_http_app)
    return app
