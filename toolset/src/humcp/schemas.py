"""Pydantic response schemas for API endpoints."""

from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# Base Tool Response Schemas
# =============================================================================


class ToolResponseBase(BaseModel):
    """Base response schema with common fields for all tools.

    All tool responses inherit from this class to ensure consistent structure:
    - success: indicates if the operation succeeded
    - error: contains error message on failure (None on success)
    """

    success: bool = Field(..., description="Whether the operation succeeded")
    error: str | None = Field(None, description="Error message on failure")


class ToolResponse[T](ToolResponseBase):
    """Generic response schema for tools with typed data field.

    Use this as a base class for tool responses:

        class MyToolResponse(ToolResponse[MyDataModel]):
            '''Response for my_tool.'''
            pass

    Or use it directly with type parameter:
        ToolResponse[MyDataModel]
    """

    data: T | None = Field(None, description="Response data on success")


class ToolSuccessResponse[T](BaseModel):
    """Success response schema for tools (data is required)."""

    success: bool = Field(True, description="Always true for success responses")
    data: T = Field(..., description="Response data")


class ToolErrorResponse(BaseModel):
    """Error response schema for tools."""

    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error message describing what went wrong")


# =============================================================================
# Type Alias Helper
# =============================================================================


def create_response_model[DataT](
    data_model: type[DataT], name: str | None = None
) -> type[ToolResponse[DataT]]:
    """Create a typed response model for a data class.

    This is a helper to create response models dynamically:

        ListBucketsResponse = create_response_model(ListBucketsData)

    Args:
        data_model: The Pydantic model for the data field.
        name: Optional name for the response class (defaults to DataModel + "Response").

    Returns:
        A new response class typed with the data model.
    """
    response_name = name or data_model.__name__.replace("Data", "Response")

    return type(
        response_name,
        (ToolResponse[data_model],),
        {
            "__doc__": f"Response schema for {data_model.__name__.replace('Data', '').lower()} tool."
        },
    )


# =============================================================================
# Shared models
# =============================================================================


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


# GET /categories response
class CategoryInfo(BaseModel):
    """Information about a category."""

    name: str = Field(..., description="Category name")
    tool_count: int = Field(..., description="Number of tools in category")
    skill: SkillFull | None = Field(None, description="Skill information if available")


class ListCategoriesResponse(BaseModel):
    """Response schema for GET /categories."""

    total_categories: int = Field(..., description="Total number of categories")
    categories: list[CategoryInfo] = Field(..., description="List of categories")
