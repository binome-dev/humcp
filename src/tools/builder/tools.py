"""Tool builder tools for creating and managing custom tools."""

from __future__ import annotations

import logging
from typing import Any

from src.humcp.decorator import tool
from src.humcp.permissions import require_auth
from src.tools.builder.manager import get_custom_tool_manager
from src.tools.builder.sandbox import (
    CompilationError,
    ExecutionError,
    TimeoutError,
    compile_code,
    execute_sandboxed,
    validate_tool_code,
)
from src.tools.builder.schemas import (
    CustomToolData,
    ToolBuilderCreateResponse,
    ToolBuilderDeleteResponse,
    ToolBuilderDisableResponse,
    ToolBuilderEnableResponse,
    ToolBuilderGetResponse,
    ToolBuilderListResponse,
    ToolBuilderTestResponse,
    ToolBuilderUpdateResponse,
    ToolDeleteData,
    ToolTestData,
)
from src.tools.builder.storage import (
    CustomToolDefinition,
    get_tool_storage,
)

logger = logging.getLogger("humcp.builder.tools")


def _to_custom_tool_data(tool_def: CustomToolDefinition) -> CustomToolData:
    """Convert CustomToolDefinition to CustomToolData."""
    return CustomToolData(
        name=tool_def.name,
        description=tool_def.description,
        code=tool_def.code,
        parameters=tool_def.parameters,
        category=tool_def.category,
        enabled=tool_def.enabled,
        created_at=tool_def.created_at.isoformat(),
        updated_at=tool_def.updated_at.isoformat(),
    )


@tool()
async def tool_builder_create(
    name: str,
    description: str,
    code: str,
    parameters: dict[str, Any] | None = None,
    category: str = "custom",
) -> ToolBuilderCreateResponse:
    """Create a new custom tool with sandboxed Python code.

        The code must define an 'execute' function that takes parameters
        and returns a dict with 'success' and 'data' or 'error' keys.

        Args:
            name: Unique name for the tool.
            description: Description of what the tool does.
            code: Python code defining an 'execute' function.
            parameters: JSON Schema for tool parameters.
            category: Tool category (default: "custom").

        Returns:
            Created tool details.

        Example:
            tool_builder_create(
                name="text_upper",
                description="Convert text to uppercase",
                parameters={"text": {"type": "string", "description": "Input text"}},
                code='''
    def execute(text: str) -> dict:
        return {"success": True, "data": {"result": text.upper()}}
    '''
            )
    """
    try:
        await require_auth()
        storage = get_tool_storage()

        # Check if tool already exists
        if await storage.exists(name):
            return ToolBuilderCreateResponse(
                success=False,
                error=f"Tool '{name}' already exists. Use tool_builder_update or delete first.",
            )

        # Validate code
        is_valid, error = validate_tool_code(code)
        if not is_valid:
            return ToolBuilderCreateResponse(
                success=False, error=f"Invalid code: {error}"
            )

        # Create tool definition
        tool_def = CustomToolDefinition(
            name=name,
            description=description,
            code=code,
            parameters=parameters or {},
            category=category,
            enabled=False,
        )

        # Save to storage
        await storage.save(tool_def)

        logger.info("Custom tool created name=%s", name)
        return ToolBuilderCreateResponse(
            success=True, data=_to_custom_tool_data(tool_def)
        )

    except Exception as e:
        logger.exception("Failed to create custom tool")
        return ToolBuilderCreateResponse(success=False, error=str(e))


@tool()
async def tool_builder_list() -> ToolBuilderListResponse:
    """List all custom tools.

    Returns:
        List of all custom tools with their details.
    """
    try:
        await require_auth()
        storage = get_tool_storage()
        tools = await storage.list_all()

        return ToolBuilderListResponse(
            success=True,
            data=[_to_custom_tool_data(t) for t in tools],
        )

    except Exception as e:
        logger.exception("Failed to list custom tools")
        return ToolBuilderListResponse(success=False, error=str(e))


@tool()
async def tool_builder_get(name: str) -> ToolBuilderGetResponse:
    """Get details of a custom tool.

    Args:
        name: Name of the tool.

    Returns:
        Tool details including code.
    """
    try:
        await require_auth()
        storage = get_tool_storage()
        tool_def = await storage.get(name)

        if tool_def is None:
            return ToolBuilderGetResponse(
                success=False, error=f"Tool '{name}' not found"
            )

        return ToolBuilderGetResponse(success=True, data=_to_custom_tool_data(tool_def))

    except Exception as e:
        logger.exception("Failed to get custom tool")
        return ToolBuilderGetResponse(success=False, error=str(e))


@tool()
async def tool_builder_delete(name: str) -> ToolBuilderDeleteResponse:
    """Delete a custom tool.

    Args:
        name: Name of the tool to delete.

    Returns:
        Confirmation of deletion.
    """
    try:
        await require_auth()
        storage = get_tool_storage()

        if not await storage.exists(name):
            return ToolBuilderDeleteResponse(
                success=False, error=f"Tool '{name}' not found"
            )

        await storage.delete(name)

        logger.info("Custom tool deleted name=%s", name)
        return ToolBuilderDeleteResponse(
            success=True,
            data=ToolDeleteData(message=f"Tool '{name}' deleted", name=name),
        )

    except Exception as e:
        logger.exception("Failed to delete custom tool")
        return ToolBuilderDeleteResponse(success=False, error=str(e))


@tool()
async def tool_builder_update(
    name: str,
    description: str | None = None,
    code: str | None = None,
    parameters: dict[str, Any] | None = None,
) -> ToolBuilderUpdateResponse:
    """Update a custom tool.

    Args:
        name: Name of the tool to update.
        description: New description (optional).
        code: New code (optional).
        parameters: New parameters schema (optional).

    Returns:
        Updated tool details.
    """
    try:
        await require_auth()
        storage = get_tool_storage()

        if not await storage.exists(name):
            return ToolBuilderUpdateResponse(
                success=False, error=f"Tool '{name}' not found"
            )

        # Validate new code if provided
        if code is not None:
            is_valid, error = validate_tool_code(code)
            if not is_valid:
                return ToolBuilderUpdateResponse(
                    success=False, error=f"Invalid code: {error}"
                )

        # Build update kwargs
        updates: dict[str, Any] = {}
        if description is not None:
            updates["description"] = description
        if code is not None:
            updates["code"] = code
        if parameters is not None:
            updates["parameters"] = parameters

        if not updates:
            return ToolBuilderUpdateResponse(success=False, error="No updates provided")

        tool_def = await storage.update(name, **updates)
        if tool_def is None:
            return ToolBuilderUpdateResponse(
                success=False, error=f"Tool '{name}' not found"
            )

        logger.info("Custom tool updated name=%s", name)
        return ToolBuilderUpdateResponse(
            success=True, data=_to_custom_tool_data(tool_def)
        )

    except Exception as e:
        logger.exception("Failed to update custom tool")
        return ToolBuilderUpdateResponse(success=False, error=str(e))


@tool()
async def tool_builder_test(
    name: str,
    params: dict[str, Any] | None = None,
) -> ToolBuilderTestResponse:
    """Test a custom tool with given parameters.

    Args:
        name: Name of the tool to test.
        params: Parameters to pass to the tool.

    Returns:
        Execution result from the tool.
    """
    try:
        await require_auth()
        storage = get_tool_storage()
        tool_def = await storage.get(name)

        if tool_def is None:
            return ToolBuilderTestResponse(
                success=False, error=f"Tool '{name}' not found"
            )

        # Compile and execute
        compiled = compile_code(tool_def.code)
        result = await execute_sandboxed(
            compiled_code=compiled,
            function_name="execute",
            params=params or {},
        )

        return ToolBuilderTestResponse(
            success=True,
            data=ToolTestData(tool_name=name, result=result),
        )

    except CompilationError as e:
        return ToolBuilderTestResponse(success=False, error=f"Compilation error: {e}")
    except TimeoutError as e:
        return ToolBuilderTestResponse(success=False, error=f"Timeout: {e}")
    except ExecutionError as e:
        return ToolBuilderTestResponse(success=False, error=f"Execution error: {e}")
    except Exception as e:
        logger.exception("Failed to test custom tool")
        return ToolBuilderTestResponse(success=False, error=str(e))


@tool()
async def tool_builder_enable(name: str) -> ToolBuilderEnableResponse:
    """Enable a custom tool for MCP/REST access.

    When enabled, the tool is registered with MCP and becomes
    available as a first-class tool.

    Args:
        name: Name of the tool to enable.

    Returns:
        Updated tool details.
    """
    try:
        await require_auth()
        storage = get_tool_storage()
        tool_def = await storage.get(name)

        if tool_def is None:
            return ToolBuilderEnableResponse(
                success=False, error=f"Tool '{name}' not found"
            )

        if tool_def.enabled:
            return ToolBuilderEnableResponse(
                success=False, error=f"Tool '{name}' is already enabled"
            )

        # Register with MCP
        manager = get_custom_tool_manager()
        if manager.is_initialized():
            if not await manager.register_tool(tool_def):
                return ToolBuilderEnableResponse(
                    success=False,
                    error=f"Failed to register tool '{name}' with MCP",
                )

        tool_def = await storage.update(name, enabled=True)
        if tool_def is None:
            return ToolBuilderEnableResponse(
                success=False, error=f"Tool '{name}' not found"
            )

        logger.info("Custom tool enabled name=%s", name)
        return ToolBuilderEnableResponse(
            success=True, data=_to_custom_tool_data(tool_def)
        )

    except Exception as e:
        logger.exception("Failed to enable custom tool")
        return ToolBuilderEnableResponse(success=False, error=str(e))


@tool()
async def tool_builder_disable(name: str) -> ToolBuilderDisableResponse:
    """Disable a custom tool from MCP/REST access.

    When disabled, the tool is unregistered from MCP.
    Note: Due to FastMCP limitations, the tool may still appear
    in the tool list until server restart.

    Args:
        name: Name of the tool to disable.

    Returns:
        Updated tool details.
    """
    try:
        await require_auth()
        storage = get_tool_storage()
        tool_def = await storage.get(name)

        if tool_def is None:
            return ToolBuilderDisableResponse(
                success=False, error=f"Tool '{name}' not found"
            )

        if not tool_def.enabled:
            return ToolBuilderDisableResponse(
                success=False, error=f"Tool '{name}' is already disabled"
            )

        # Unregister from MCP
        manager = get_custom_tool_manager()
        if manager.is_initialized():
            await manager.unregister_tool(name)

        tool_def = await storage.update(name, enabled=False)
        if tool_def is None:
            return ToolBuilderDisableResponse(
                success=False, error=f"Tool '{name}' not found"
            )

        logger.info("Custom tool disabled name=%s", name)
        return ToolBuilderDisableResponse(
            success=True, data=_to_custom_tool_data(tool_def)
        )

    except Exception as e:
        logger.exception("Failed to disable custom tool")
        return ToolBuilderDisableResponse(success=False, error=str(e))
