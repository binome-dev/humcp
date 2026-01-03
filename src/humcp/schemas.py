"""Pydantic response schemas for API endpoints."""

from typing import Any

from pydantic import BaseModel, Field


# Shared models
class ToolSummary(BaseModel):
    """Summary of a tool in listings."""

    name: str = Field(..., description="Tool name")
    description: str | None = Field(None, description="Tool description")
    endpoint: str = Field(..., description="API endpoint path")


class SkillMetadata(BaseModel):
    """Skill metadata (name and description only)."""

    name: str = Field(..., description="Skill name")
    description: str = Field(..., description="Skill description")


class SkillFull(BaseModel):
    """Full skill information including content."""

    name: str = Field(..., description="Skill name")
    description: str = Field(..., description="Skill description")
    content: str = Field(..., description="Skill markdown content")


# GET /tools response
class CategorySummary(BaseModel):
    """Summary of a category in the tools listing."""

    count: int = Field(..., description="Number of tools in category")
    tools: list[ToolSummary] = Field(..., description="List of tools")
    skill: SkillMetadata | None = Field(None, description="Skill metadata if available")


class ListToolsResponse(BaseModel):
    """Response schema for GET /tools."""

    total_tools: int = Field(..., description="Total number of tools")
    categories: dict[str, CategorySummary] = Field(
        ..., description="Tools grouped by category"
    )


# GET /tools/{category} response
class GetCategoryResponse(BaseModel):
    """Response schema for GET /tools/{category}."""

    category: str = Field(..., description="Category name")
    count: int = Field(..., description="Number of tools in category")
    tools: list[ToolSummary] = Field(..., description="List of tools")
    skill: SkillFull | None = Field(None, description="Full skill information")


# GET /tools/{category}/{tool_name} response
class InputSchema(BaseModel):
    """JSON Schema for tool input."""

    type: str = Field(default="object", description="Schema type")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Property definitions"
    )
    required: list[str] = Field(default_factory=list, description="Required properties")


class GetToolResponse(BaseModel):
    """Response schema for GET /tools/{category}/{tool_name}."""

    name: str = Field(..., description="Tool name")
    category: str = Field(..., description="Tool category")
    description: str | None = Field(None, description="Tool description")
    endpoint: str = Field(..., description="API endpoint path")
    input_schema: InputSchema = Field(..., description="JSON Schema for tool input")
    output_schema: dict[str, Any] | None = Field(
        description="JSON schema for tool output", default=None
    )
