"""Pydantic output schemas for tool builder tools."""

from typing import Any

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# Custom Tool Data Schemas
# =============================================================================


class CustomToolData(BaseModel):
    """Data representing a custom tool definition."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    code: str = Field(..., description="Python code for the tool")
    parameters: dict[str, Any] = Field(
        ..., description="JSON Schema for tool parameters"
    )
    category: str = Field(..., description="Tool category")
    enabled: bool = Field(..., description="Whether the tool is enabled")
    created_at: str | None = Field(None, description="Creation timestamp")
    updated_at: str | None = Field(None, description="Last update timestamp")


class ToolDeleteData(BaseModel):
    """Output data for tool deletion."""

    message: str = Field(..., description="Success message")
    name: str = Field(..., description="Name of the deleted tool")


class ToolTestData(BaseModel):
    """Output data for tool_builder_test."""

    tool_name: str = Field(..., description="Name of the tested tool")
    result: Any = Field(..., description="Execution result from the tool")


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class ToolBuilderCreateResponse(ToolResponse[CustomToolData]):
    """Response schema for tool_builder_create tool."""

    pass


class ToolBuilderListResponse(ToolResponse[list[CustomToolData]]):
    """Response schema for tool_builder_list tool."""

    pass


class ToolBuilderGetResponse(ToolResponse[CustomToolData]):
    """Response schema for tool_builder_get tool."""

    pass


class ToolBuilderDeleteResponse(ToolResponse[ToolDeleteData]):
    """Response schema for tool_builder_delete tool."""

    pass


class ToolBuilderUpdateResponse(ToolResponse[CustomToolData]):
    """Response schema for tool_builder_update tool."""

    pass


class ToolBuilderTestResponse(ToolResponse[ToolTestData]):
    """Response schema for tool_builder_test tool."""

    pass


class ToolBuilderEnableResponse(ToolResponse[CustomToolData]):
    """Response schema for tool_builder_enable tool."""

    pass


class ToolBuilderDisableResponse(ToolResponse[CustomToolData]):
    """Response schema for tool_builder_disable tool."""

    pass
