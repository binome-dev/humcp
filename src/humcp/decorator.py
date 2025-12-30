"""Tool decorator for registering MCP tools."""

import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.humcp.registry import _TOOL_NAMES, TOOL_REGISTRY, ToolRegistration

__all__ = ["tool"]


def tool(
    name: str | None = None, category: str | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to register a function as an MCP tool.

    Args:
        name: Tool name. Defaults to "{category}_{function_name}".
        category: Tool category. Defaults to parent folder name.

    Raises:
        ValueError: If a tool with the same name already exists.

    Example:
        # In src/tools/local/calculator.py
        @tool()  # name="local_add", category="local"
        async def add(a: float, b: float) -> dict:
            return {"success": True, "data": {"result": a + b}}

        @tool("my_tool", category="custom")  # explicit name and category
        async def func() -> dict:
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Determine category from parent folder name
        if category:
            tool_category = category
        else:
            tool_category = _get_category_from_path(func)

        # Determine name
        tool_name = name or f"{tool_category}_{func.__name__}"

        # Check for duplicate names
        if tool_name in _TOOL_NAMES:
            raise ValueError(f"Duplicate tool name: '{tool_name}' already registered")

        _TOOL_NAMES.add(tool_name)
        TOOL_REGISTRY.append(ToolRegistration(tool_name, tool_category, func))
        return func

    return decorator


def _get_category_from_path(func: Callable[..., Any]) -> str:
    """Get category from function's file immediate parent folder name."""
    try:
        file_path = Path(inspect.getfile(func))
        return file_path.parent.name
    except (TypeError, OSError):
        return "uncategorized"
