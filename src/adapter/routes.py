from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastmcp.client import Client
from mcp.types import Tool

from .models import create_pydantic_model_from_schema, sanitize_model_name


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

                result = await self.client.call_tool(tool.name, params)

                if hasattr(result, "content"):
                    if isinstance(result.content, list):
                        return {
                            "result": [
                                item.text if hasattr(item, "text") else str(item)
                                for item in result.content
                            ]
                        }
                    return {"result": result.content}
                return {"result": str(result)}

            except HTTPException:
                raise
            except Exception as e:
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

    def _get_tool_categories(self) -> dict[str, dict[str, Any]]:
        categories: dict[str, dict[str, Any]] = {}

        for tool_name, tool in self.tools.items():
            parts = tool_name.split("/")
            if len(parts) >= 2:
                category = parts[0]
                sub_tool = "/".join(parts[1:])
            else:
                category = "uncategorized"
                sub_tool = tool_name

            if category not in categories:
                categories[category] = {"name": category, "tools_count": 0, "tools": []}

            categories[category]["tools_count"] += 1
            categories[category]["tools"].append(
                {
                    "name": sub_tool,
                    "full_name": tool_name,
                    "description": tool.description,
                    "endpoint": f"{self.route_prefix}/{tool_name}",
                }
            )

        return categories

    def create_info_routes(self, app: FastAPI):
        @app.get(f"{self.route_prefix}", tags=["Info"])
        async def list_tools():
            categories = self._get_tool_categories()

            return {
                "total_tools": len(self.tools),
                "categories_count": len(categories),
                "tools_by_category": {
                    category_name: {
                        "tools_count": category_data["tools_count"],
                        "tools": [
                            {
                                "name": tool["name"],
                                "full_name": tool["full_name"],
                                "description": tool["description"],
                                "endpoint": tool["endpoint"],
                            }
                            for tool in category_data["tools"]
                        ],
                    }
                    for category_name, category_data in sorted(categories.items())
                },
            }

        @app.get(f"{self.route_prefix}/{{category}}", tags=["Info"])
        async def get_category_tools(category: str):
            categories = self._get_tool_categories()

            if category not in categories:
                raise HTTPException(
                    status_code=404,
                    detail=f"Category '{category}' not found. Available categories: {', '.join(sorted(categories.keys()))}",
                )

            category_data = categories[category]
            return {
                "category": category,
                "tools_count": category_data["tools_count"],
                "tools": [
                    {
                        "name": tool["name"],
                        "full_name": tool["full_name"],
                        "description": tool["description"],
                        "parameters": self.tools[tool["full_name"]].inputSchema
                        if hasattr(self.tools[tool["full_name"]], "inputSchema")
                        else {},
                        "endpoint": tool["endpoint"],
                    }
                    for tool in category_data["tools"]
                ],
            }

        # Tool detail endpoint
        @app.get(f"{self.route_prefix}/{{category}}/{{tool_name:path}}", tags=["Info"])
        async def get_tool_info(category: str, tool_name: str):
            full_tool_name = f"{category}/{tool_name}"

            if full_tool_name not in self.tools:
                raise HTTPException(
                    status_code=404, detail=f"Tool '{full_tool_name}' not found"
                )

            tool = self.tools[full_tool_name]
            input_schema = tool.inputSchema if hasattr(tool, "inputSchema") else {}

            return {
                "name": tool.name,
                "category": category,
                "description": tool.description,
                "parameters": input_schema,
                "endpoint": f"{self.route_prefix}/{tool.name}",
            }
