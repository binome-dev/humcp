import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from src.adapter.adapter import FastMCPFastAPIAdapter
from src.server import mcp

load_dotenv()

# Single port for both FastAPI (Swagger) and MCP ASGI app
APP_PORT = os.getenv("PORT", os.getenv("MCP_PORT", "8080"))

# MCP ASGI app that will be mounted under /mcp
mcp_http_app = mcp.http_app(path="/")

# URL shown in the API info response (override with MCP_SERVER_URL if needed)
mcp_server_url = os.getenv("MCP_SERVER_URL") or f"http://0.0.0.0:{APP_PORT}/mcp"

adapter = FastMCPFastAPIAdapter(
    title="HuMCP FastAPI server",
    description="HuMCP FastAPI server",
    mcp_transport=mcp,  # use in-memory transport for route generation/calls
    transport="http",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the MCP ASGI app runs its lifespan so /mcp works when mounted
    async with mcp_http_app.router.lifespan_context(mcp_http_app):
        await adapter._load_tools()
        adapter._register_routes(app)
        adapter.route_generator.create_info_routes(app)
        yield
        await adapter._cleanup()


app = FastAPI(
    title=adapter.title,
    description=adapter.description,
    version=adapter.version,
    lifespan=lifespan,
)


# Root info endpoint (mirrors the adapter's default)
@app.get("/", tags=["Info"])
async def root():
    tools = adapter.route_generator.tools

    # Derive tool categories from the public tools attribute instead of using
    # the private _get_tool_categories() helper.
    if hasattr(tools, "items"):
        # tools is already a mapping of {category: [tools...]}
        categories = tools
    else:
        # tools is an iterable of tool objects; group by their "category" attribute
        categories = {}
        for tool in tools or []:
            category = getattr(tool, "category", "default")
            categories.setdefault(category, []).append(tool)
    return {
        "name": adapter.title,
        "version": adapter.version,
        "mcp_server": adapter.mcp_display_url or mcp_server_url,
        "tools_count": len(adapter.route_generator.tools),
        "categories_count": len(categories),
        "route_prefix": adapter.route_generator.route_prefix,
        "available_categories": sorted(categories.keys()),
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "tools_list": f"{adapter.route_generator.route_prefix}",
            "category_tools": f"{adapter.route_generator.route_prefix}/{{category}}",
            "tool_info": f"{adapter.route_generator.route_prefix}/{{category}}/{{tool_name}}",
            "mcp": "/mcp",
        },
    }


# Mount MCP under /mcp on the same port as FastAPI/Swagger
app.mount("/mcp", mcp_http_app)
