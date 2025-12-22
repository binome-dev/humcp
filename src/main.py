import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from src.adapter.fast_mcp_fast_api_adapter import FastMCPFastAPIAdapter
from src.logging_setup import configure_logging
from src.mcp_register import create_mcp_server

load_dotenv()
configure_logging()

APP_PORT = os.getenv("PORT", os.getenv("MCP_PORT", "8080"))
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL") or f"http://0.0.0.0:{APP_PORT}/mcp"

mcp = create_mcp_server()
mcp_http_app = mcp.http_app(path="/")

adapter = FastMCPFastAPIAdapter(
    title="HuMCP FastAPI server",
    description="HuMCP FastAPI server",
    mcp_transport=mcp,
    transport="http",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp_http_app.router.lifespan_context(mcp_http_app):
        await adapter._load_tools()
        adapter._register_routes(app)
        yield
        await adapter._cleanup()


app = FastAPI(
    title=adapter.title,
    description=adapter.description,
    version=adapter.version,
    lifespan=lifespan,
)


@app.get("/", tags=["Info"])
async def root():
    categories = adapter.route_generator._get_tool_categories()
    return {
        "name": adapter.title,
        "version": adapter.version,
        "mcp_server": adapter.mcp_display_url or MCP_SERVER_URL,
        "tools_count": len(adapter.route_generator.tools),
        "categories": list(categories.keys()),
        "endpoints": {
            "docs": "/docs",
            "openapi": "/openapi.json",
            "tools": adapter.route_generator.route_prefix,
            "mcp": "/mcp",
        },
    }


app.mount("/mcp", mcp_http_app)
