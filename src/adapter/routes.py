import logging
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastmcp.client import Client
from mcp.types import Tool

from .models import create_pydantic_model_from_schema, sanitize_model_name

logger = logging.getLogger("humcp.adapter.routes")


class RouteGenerator:
    def __init__(
        self,
        client: Client,
        route_prefix: str = "/tools",
        tags: list[str] | None = None,
    ):
        self.client = client
        self.route_prefix = route_prefix.rstrip("/")
        self.tags = tags or ["MCP Tools"]
        self.tools: dict[str, Tool] = {}

    async def load_tools(self) -> dict[str, Tool]:
        tools_list: list[Tool] = await self.client.list_tools()
        self.tools = {tool.name: tool for tool in tools_list}
        logger.info("Discovered %d tools from MCP server", len(self.tools))
        return self.tools

    def register_routes(self, app: FastAPI):
        for _tool_name, tool in self.tools.items():
            self._register_tool_route(app, tool)

    def _register_tool_route(self, app: FastAPI, tool: Tool):
        # Create Pydantic model for input validation
        model_name = f"{sanitize_model_name(tool.name)}Input"
        # MCP protocol uses inputSchema
        input_schema = tool.inputSchema if hasattr(tool, "inputSchema") else {}
        InputModel = create_pydantic_model_from_schema(
            input_schema, model_name, description=f"Input parameters for {tool.name}"
        )

        async def tool_endpoint(input_data: InputModel = Body(...)) -> dict[str, Any]:
            try:
                params = input_data.model_dump(exclude_none=True)
                logger.info(
                    "Invoking tool %s with params keys=%s",
                    tool.name,
                    list(params.keys()),
                )

                result = await self.client.call_tool(tool.name, params)

                if hasattr(result, "content"):
                    if isinstance(result.content, list):
                        logger.info(
                            "Tool %s returned list content length=%d",
                            tool.name,
                            len(result.content),
                        )
                        return {
                            "result": [
                                item.text if hasattr(item, "text") else str(item)
                                for item in result.content
                            ]
                        }
                    logger.info(
                        "Tool %s returned content type=%s",
                        tool.name,
                        type(result.content).__name__,
                    )
                    return {"result": result.content}
                logger.info("Tool %s returned non-content result", tool.name)
                return {"result": str(result)}

            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Tool execution failed: %s", tool.name)
                raise HTTPException(
                    status_code=500, detail=f"Tool execution failed: {str(e)}"
                ) from e

        route_path = f"{self.route_prefix}/{tool.name}"
        app.add_api_route(
            path=route_path,
            endpoint=tool_endpoint,
            methods=["POST"],
            response_model=dict[str, Any],
            summary=tool.description or f"Execute {tool.name}",
            description=tool.description,
            tags=self.tags,
            name=tool.name,
        )

    def _get_tool_categories(self) -> dict[str, list[dict[str, Any]]]:
        categories: dict[str, list[dict[str, Any]]] = {}

        for tool_name, tool in self.tools.items():
            parts = tool_name.split("/", 1)
            category = parts[0] if len(parts) > 1 else "uncategorized"
            short_name = parts[1] if len(parts) > 1 else tool_name

            categories.setdefault(category, []).append(
                {
                    "name": short_name,
                    "full_name": tool_name,
                    "description": tool.description,
                    "endpoint": f"{self.route_prefix}/{tool_name}",
                }
            )

        return categories

    def _get_input_schema(self, tool: Tool) -> dict:
        return tool.inputSchema if hasattr(tool, "inputSchema") else {}

    def create_info_routes(self, app: FastAPI):
        @app.get(f"{self.route_prefix}", tags=["Info"])
        async def list_tools():
            categories = self._get_tool_categories()
            return {
                "total_tools": len(self.tools),
                "categories": {
                    name: {"count": len(tools), "tools": tools}
                    for name, tools in sorted(categories.items())
                },
            }

        @app.get(f"{self.route_prefix}/{{category}}", tags=["Info"])
        async def get_category_tools(category: str):
            categories = self._get_tool_categories()
            if category not in categories:
                raise HTTPException(
                    status_code=404,
                    detail=f"Category '{category}' not found",
                )
            tools = categories[category]
            return {
                "category": category,
                "count": len(tools),
                "tools": [
                    {
                        **t,
                        "parameters": self._get_input_schema(
                            self.tools[t["full_name"]]
                        ),
                    }
                    for t in tools
                ],
            }

        @app.get(f"{self.route_prefix}/{{category}}/{{tool_name:path}}", tags=["Info"])
        async def get_tool_info(category: str, tool_name: str):
            full_name = f"{category}/{tool_name}"
            if full_name not in self.tools:
                raise HTTPException(
                    status_code=404, detail=f"Tool '{full_name}' not found"
                )

            tool = self.tools[full_name]
            return {
                "name": tool.name,
                "category": category,
                "description": tool.description,
                "parameters": self._get_input_schema(tool),
                "endpoint": f"{self.route_prefix}/{tool.name}",
            }
