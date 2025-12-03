from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI
from fastmcp.client import Client

from .routes import RouteGenerator


class FastMCPFastAPIAdapter:
    def __init__(
        self,
        mcp_url: str,
        transport: str = "http",
        title: str = "FastMCPFastAPIAdapter",
        description: str = "Auto-generated FastAPI interface for FastMCP server tools",
        version: str = "1.0.0",
        route_prefix: str = "/tools",
        tags: Optional[List[str]] = None
    ):
        self.title = title
        self.description = description
        self.version = version
        self.route_prefix = route_prefix
        self.tags = tags or ["MCP Tools"]

        self.mcp_url = self._construct_url(mcp_url, transport)

        self.mcp_client = Client(self.mcp_url)
        self.route_generator = RouteGenerator(
            client=self.mcp_client,
            route_prefix=route_prefix,
            tags=self.tags
        )

    def _construct_url(self, base_url: str, transport: str) -> str:
        base_url = base_url.rstrip("/")

        if base_url.endswith(f"/{transport}"):
            return base_url

        if transport == "http":
            return f"{base_url}/mcp"
        elif transport == "sse":
            return f"{base_url}/sse"
        elif transport == "stdio":
            return base_url
        else:
            return f"{base_url}/{transport}"

    async def _load_tools(self):
        await self.mcp_client.__aenter__()
        await self.route_generator.load_tools()
        print(f"Loaded {len(self.route_generator.tools)} tools from FastMCP server")

    def _register_routes(self, app: FastAPI):
        self.route_generator.register_routes(app)
        self.route_generator.create_info_routes(app)

    async def _cleanup(self):
        await self.mcp_client.__aexit__(None, None, None)

    def create_app(self) -> FastAPI:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await self._load_tools()
            self._register_routes(app)
            yield
            await self._cleanup()

        app = FastAPI(
            title=self.title,
            description=self.description,
            version=self.version,
            lifespan=lifespan,
        )

        # Add root endpoint
        @app.get("/", tags=["Info"])
        async def root():
            categories = self.route_generator._get_tool_categories()
            return {
                "name": self.title,
                "version": self.version,
                "mcp_server": self.mcp_url,
                "tools_count": len(self.route_generator.tools),
                "categories_count": len(categories),
                "route_prefix": self.route_generator.route_prefix,
                "available_categories": sorted(categories.keys()),
                "endpoints": {
                    "docs": "/docs",
                    "redoc": "/redoc",
                    "openapi": "/openapi.json",
                    "tools_list": f"{self.route_generator.route_prefix}",
                    "category_tools": f"{self.route_generator.route_prefix}/{{category}}",
                    "tool_info": f"{self.route_generator.route_prefix}/{{category}}/{{tool_name}}"
                }
            }

        return app