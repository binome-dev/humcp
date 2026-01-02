"""REST route generation for tools."""

import logging
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, Field, create_model

from src.humcp.decorator import RegisteredTool
from src.humcp.schemas import (
    CategorySummary,
    GetCategoryResponse,
    GetToolResponse,
    InputSchema,
    ListToolsResponse,
    SkillFull,
    SkillMetadata,
    ToolSummary,
)
from src.humcp.skills import discover_skills

logger = logging.getLogger("humcp.routes")


def _format_tag(category: str) -> str:
    """Format category as display tag: 'local_files' -> 'Local Files'."""
    return category.replace("_", " ").title()


def register_routes(
    app: FastAPI,
    tools_path: Path,
    tools: list[RegisteredTool],
) -> None:
    """Register REST routes for tools."""
    # Build lookups
    categories = _build_categories(tools)
    tool_lookup = {(t.category, t.tool.name): t for t in tools}

    # Tool execution endpoints
    for reg in tools:
        _add_tool_route(app, reg)

    # Discover skills
    skills = discover_skills(tools_path)

    # Info endpoints
    @app.get("/tools", tags=["Info"], response_model=ListToolsResponse)
    async def list_tools() -> ListToolsResponse:
        return ListToolsResponse(
            total_tools=len(tools),
            categories={
                cat: CategorySummary(
                    count=len(items),
                    tools=[ToolSummary(**t) for t in items],
                    skill=SkillMetadata(
                        name=skills[cat].name, description=skills[cat].description
                    )
                    if cat in skills
                    else None,
                )
                for cat, items in sorted(categories.items())
            },
        )

    @app.get("/tools/{category}", tags=["Info"], response_model=GetCategoryResponse)
    async def get_category(category: str) -> GetCategoryResponse:
        if category not in categories:
            raise HTTPException(404, f"Category '{category}' not found")
        skill = skills.get(category)
        return GetCategoryResponse(
            category=category,
            count=len(categories[category]),
            tools=[ToolSummary(**t) for t in categories[category]],
            skill=SkillFull(
                name=skill.name, description=skill.description, content=skill.content
            )
            if skill
            else None,
        )

    @app.get(
        "/tools/{category}/{tool_name}", tags=["Info"], response_model=GetToolResponse
    )
    async def get_tool(category: str, tool_name: str) -> GetToolResponse:
        reg = tool_lookup.get((category, tool_name))
        if not reg:
            raise HTTPException(404, f"Tool '{tool_name}' not found in '{category}'")
        return GetToolResponse(
            name=reg.tool.name,
            category=reg.category,
            description=reg.tool.description,
            endpoint=f"/tools/{reg.tool.name}",
            input_schema=InputSchema(**reg.tool.parameters),
            output_schema=reg.tool.output_schema,
        )


def _add_tool_route(app: FastAPI, reg: RegisteredTool) -> None:
    """Add POST /tools/{name} endpoint for a tool."""
    tool = reg.tool
    InputModel = _create_model_from_schema(
        tool.parameters, f"{_pascal(tool.name)}Input"
    )

    async def endpoint(data: BaseModel = Body(...)) -> dict[str, Any]:
        try:
            params = data.model_dump(exclude_none=True)
            result = await tool.fn(**params)
            return {"result": result}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Tool %s failed", tool.name)
            raise HTTPException(500, "Tool execution failed") from e

    endpoint.__annotations__["data"] = InputModel
    app.add_api_route(
        f"/tools/{tool.name}",
        endpoint,
        methods=["POST"],
        summary=tool.description or tool.name,
        tags=[_format_tag(reg.category)],
        name=tool.name,
    )


def _build_categories(tools: list[RegisteredTool]) -> dict[str, list[dict[str, Any]]]:
    """Build category -> tools map."""
    cats: dict[str, list[dict[str, Any]]] = {}
    for reg in tools:
        cats.setdefault(reg.category, []).append(
            {
                "name": reg.tool.name,
                "description": reg.tool.description,
                "endpoint": f"/tools/{reg.tool.name}",
            }
        )
    return cats


def build_openapi_tags(tools: list[RegisteredTool]) -> list[dict[str, str]]:
    """Build OpenAPI tag metadata."""
    categories = sorted({reg.category for reg in tools})
    tags = [{"name": "Info", "description": "Server and tool information"}]
    for cat in categories:
        count = sum(1 for reg in tools if reg.category == cat)
        tags.append(
            {
                "name": _format_tag(cat),
                "description": f"{_format_tag(cat)} tools ({count} endpoints)",
            }
        )
    return tags


def _pascal(name: str) -> str:
    """Convert to PascalCase."""
    name = name.replace("_", " ").replace("-", " ").replace(".", " ")
    name = "".join(w.capitalize() for w in name.split())
    return f"Model{name}" if name and not name[0].isalpha() else name or "Model"


def _create_model_from_schema(schema: dict[str, Any], name: str) -> type[BaseModel]:
    """Create Pydantic model from JSON schema."""
    if schema.get("type") != "object":
        return create_model(name, value=(Any, ...))

    props = schema.get("properties", {})
    required = schema.get("required", [])
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

    return create_model(name, **fields)
