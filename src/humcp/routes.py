"""REST route generation for tools."""

import logging
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastmcp.client import Client
from mcp.types import Tool
from pydantic import BaseModel, Field, create_model

logger = logging.getLogger("humcp.routes")


def register_routes(app: FastAPI, client: Client, tools: dict[str, Tool]) -> None:
    """Register all REST routes for tools.

    Args:
        app: FastAPI application.
        client: MCP client for tool execution.
        tools: Dict of tool name to Tool object.
    """
    # Tool execution endpoints
    for tool in tools.values():
        _add_tool_route(app, client, tool)

    # Info endpoints
    @app.get("/tools", tags=["Info"])
    async def list_tools():
        cats = _categorize(tools)
        return {
            "total_tools": len(tools),
            "categories": {
                k: {"count": len(v), "tools": v} for k, v in sorted(cats.items())
            },
        }

    @app.get("/tools/{category}", tags=["Info"])
    async def get_category(category: str):
        cats = _categorize(tools)
        if category not in cats:
            raise HTTPException(404, f"Category '{category}' not found")
        return {
            "category": category,
            "count": len(cats[category]),
            "tools": [
                {**t, "parameters": _get_schema(tools[t["full_name"]])}
                for t in cats[category]
            ],
        }

    @app.get("/tools/{category}/{tool_name}", tags=["Info"])
    async def get_tool(category: str, tool_name: str):
        full = f"{category}_{tool_name}"
        if full not in tools:
            raise HTTPException(404, f"Tool '{full}' not found")
        t = tools[full]
        return {
            "name": t.name,
            "category": category,
            "description": t.description,
            "parameters": _get_schema(t),
            "endpoint": f"/tools/{t.name}",
        }


def _add_tool_route(app: FastAPI, client: Client, tool: Tool) -> None:
    """Add POST /tools/{name} endpoint for a tool."""
    schema = _get_schema(tool)
    InputModel = _create_model(schema, f"{_pascal(tool.name)}Input")

    async def endpoint(data: BaseModel = Body(...)) -> dict[str, Any]:  # type: ignore[assignment]
        try:
            result = await client.call_tool(
                tool.name, data.model_dump(exclude_none=True)
            )
            if hasattr(result, "content") and isinstance(result.content, list):
                return {
                    "result": [
                        x.text if hasattr(x, "text") else str(x) for x in result.content
                    ]
                }
            return {"result": getattr(result, "content", str(result))}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Tool %s failed", tool.name)
            raise HTTPException(500, f"Tool failed: {e}") from e

    endpoint.__annotations__["data"] = InputModel
    app.add_api_route(
        f"/tools/{tool.name}",
        endpoint,
        methods=["POST"],
        summary=tool.description or tool.name,
        tags=["Tools"],
        name=tool.name,
    )


def _categorize(tools: dict[str, Tool]) -> dict[str, list[dict[str, Any]]]:
    """Group tools by category prefix."""
    cats: dict[str, list[dict[str, Any]]] = {}
    for name, t in tools.items():
        parts = name.split("_", 1)
        cat = parts[0] if len(parts) > 1 else "uncategorized"
        short = parts[1] if len(parts) > 1 else name
        cats.setdefault(cat, []).append(
            {
                "name": short,
                "full_name": name,
                "description": t.description,
                "endpoint": f"/tools/{name}",
            }
        )
    return cats


def _get_schema(tool: Tool) -> dict[str, Any]:
    """Get input schema from tool."""
    return tool.inputSchema if hasattr(tool, "inputSchema") else {}


def _pascal(name: str) -> str:
    """Convert to PascalCase."""
    name = name.replace("_", " ").replace("-", " ").replace(".", " ")
    name = "".join(w.capitalize() for w in name.split())
    return f"Model{name}" if name and not name[0].isalpha() else name or "Model"


def _create_model(schema: dict[str, Any], name: str) -> type[BaseModel]:
    """Create Pydantic model from JSON schema."""
    if schema.get("type") != "object":
        return create_model(name, value=(Any, ...))  # type: ignore[call-overload]

    props: dict[str, Any] = schema.get("properties", {})
    required: list[str] = schema.get("required", [])
    fields: dict[str, Any] = {}

    type_map = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    for fname, fschema in props.items():
        ftype = type_map.get(fschema.get("type"), Any)
        desc = fschema.get("description")
        if fname in required:
            fields[fname] = (
                (ftype, Field(..., description=desc)) if desc else (ftype, ...)
            )
        else:
            fields[fname] = (
                (ftype | None, Field(None, description=desc))
                if desc
                else (ftype | None, None)
            )

    return create_model(name, **fields)  # type: ignore[call-overload]
