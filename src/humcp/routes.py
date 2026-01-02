"""REST route generation for tools."""

import inspect
import logging
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, Field, create_model

from src.humcp.registry import TOOL_REGISTRY, ToolRegistration

logger = logging.getLogger("humcp.routes")


def _format_tag(category: str) -> str:
    """Format category name as a display-friendly tag.

    Converts snake_case or lowercase to Title Case.
    E.g., "google" -> "Google", "local_files" -> "Local Files"
    """
    return category.replace("_", " ").title()


def register_routes(app: FastAPI) -> None:
    """Register REST routes from TOOL_REGISTRY.

    Args:
        app: FastAPI application.
    """
    # Tool execution endpoints
    for reg in TOOL_REGISTRY:
        _add_tool_route(app, reg)

    # Build cached lookup structures once at startup
    categories = _build_categories()
    tool_lookup = _build_tool_lookup()
    total_tools = len(TOOL_REGISTRY)

    # Info endpoints
    @app.get("/tools", tags=["Info"])
    async def list_tools():
        return {
            "total_tools": total_tools,
            "categories": {
                k: {"count": len(v), "tools": v} for k, v in sorted(categories.items())
            },
        }

    @app.get("/tools/{category}", tags=["Info"])
    async def get_category(category: str):
        if category not in categories:
            raise HTTPException(404, f"Category '{category}' not found")
        return {
            "category": category,
            "count": len(categories[category]),
            "tools": categories[category],
        }

    @app.get("/tools/{category}/{tool_name}", tags=["Info"])
    async def get_tool(category: str, tool_name: str):
        # Try exact match first, then with category prefix
        reg = tool_lookup.get((category, tool_name)) or tool_lookup.get(
            (category, f"{category}_{tool_name}")
        )
        if not reg:
            raise HTTPException(
                404, f"Tool '{tool_name}' not found in category '{category}'"
            )
        return {
            "name": reg.name,
            "category": reg.category,
            "description": reg.func.__doc__,
            "endpoint": f"/tools/{reg.name}",
            "input_schema": _get_schema_from_func(reg.func),
        }


def _add_tool_route(app: FastAPI, reg: ToolRegistration) -> None:
    """Add POST /tools/{name} endpoint for a tool."""
    schema = _get_schema_from_func(reg.func)
    InputModel = _create_model(schema, f"{_pascal(reg.name)}Input")

    async def endpoint(data: BaseModel = Body(...)) -> dict[str, Any]:  # type: ignore[assignment]
        try:
            params = data.model_dump(exclude_none=True)
            result = await reg.func(**params)
            return {"result": result}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Tool %s failed", reg.name)
            raise HTTPException(500, f"Tool failed: {e}") from e

    endpoint.__annotations__["data"] = InputModel
    app.add_api_route(
        f"/tools/{reg.name}",
        endpoint,
        methods=["POST"],
        summary=reg.func.__doc__ or reg.name,
        tags=[_format_tag(reg.category)],
        name=reg.name,
    )


def _build_categories() -> dict[str, list[dict[str, Any]]]:
    """Build category map from TOOL_REGISTRY (called once at startup)."""
    cats: dict[str, list[dict[str, Any]]] = {}
    for reg in TOOL_REGISTRY:
        cats.setdefault(reg.category, []).append(
            {
                "name": reg.name,
                "description": reg.func.__doc__,
                "endpoint": f"/tools/{reg.name}",
            }
        )
    return cats


def build_openapi_tags() -> list[dict[str, str]]:
    """Build OpenAPI tag metadata for all tool categories.

    Returns a list of tag definitions with name and description,
    sorted alphabetically by tag name. Includes the "Info" tag first.
    """
    # Collect unique categories
    categories = sorted({reg.category for reg in TOOL_REGISTRY})

    # Build tag metadata
    tags = [
        {"name": "Info", "description": "Server and tool information endpoints"},
    ]

    for category in categories:
        # Count tools in this category
        tool_count = sum(1 for reg in TOOL_REGISTRY if reg.category == category)
        tags.append(
            {
                "name": _format_tag(category),
                "description": f"{_format_tag(category)} tools ({tool_count} endpoints)",
            }
        )

    return tags


def _build_tool_lookup() -> dict[tuple[str, str], ToolRegistration]:
    """Build (category, name) -> ToolRegistration lookup (called once at startup)."""
    return {(reg.category, reg.name): reg for reg in TOOL_REGISTRY}


def _get_schema_from_func(func: Any) -> dict[str, Any]:
    """Extract JSON schema from function type hints."""

    sig = inspect.signature(func)
    properties: dict[str, Any] = {}
    required: list[str] = []

    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    for name, param in sig.parameters.items():
        if param.annotation != inspect.Parameter.empty:
            # Get base type (handle Optional, etc.)
            ann = param.annotation
            # Skip parameters that are explicitly annotated as None.
            # Optional[...] / Union[..., None] are handled in the Union logic below.
            if ann is type(None):
                continue

            # Handle Union types (e.g., str | None)
            args = getattr(ann, "__args__", None)
            if args:
                ann = next((a for a in args if a is not type(None)), ann)

            json_type = type_map.get(ann, "string")
            properties[name] = {"type": json_type}

            if param.default == inspect.Parameter.empty:
                required.append(name)

    return {"type": "object", "properties": properties, "required": required}


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
