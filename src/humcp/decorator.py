"""Tool decorator and registration types for MCP tools.

The @tool decorator marks functions with name and category metadata.
FastMCP handles description and schema generation.
"""

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple

from fastmcp.tools import FunctionTool

__all__ = [
    "tool",
    "is_tool",
    "get_tool_name",
    "get_tool_category",
    "RegisteredTool",
    "ToolMetadata",
]

TOOL_ATTR = "_humcp_tool"


@dataclass(frozen=True)
class ToolMetadata:
    """Metadata stored on decorated functions."""

    name: str
    category: str


class RegisteredTool(NamedTuple):
    """A tool registered with FastMCP, with category for grouping.

    Attributes:
        tool: The FastMCP FunctionTool object (has name, description, parameters, fn).
        category: Category for REST endpoint grouping.
    """

    tool: FunctionTool
    category: str


def tool(
    tool_name: str | None = None,
    category: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Mark a function as an MCP tool.

    Args:
        tool_name: Tool name for MCP registration. Defaults to function name.
        category: Tool category for grouping. Defaults to parent folder name.

    Example:
        @tool()  # name from function, category from file path
        async def add(a: float, b: float) -> dict:
            return {"result": a + b}

        @tool("calculator_add", "math")  # explicit name and category
        async def multiply(a: float, b: float) -> dict:
            return {"result": a * b}
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Resolve name (default to function name)
        resolved_name = tool_name if tool_name is not None else func.__name__

        # Resolve category (default to parent folder name)
        resolved_category = category
        if resolved_category is None:
            try:
                file_path = Path(inspect.getfile(func))
                resolved_category = file_path.parent.name
            except (TypeError, OSError):
                resolved_category = "uncategorized"

        metadata = ToolMetadata(name=resolved_name, category=resolved_category)
        setattr(func, TOOL_ATTR, metadata)
        return func

    return decorator


def is_tool(func: Any) -> bool:
    """Check if a function is marked as a tool."""
    return hasattr(func, TOOL_ATTR)


def get_tool_name(func: Callable[..., Any]) -> str:
    """Get tool name from a decorated function."""
    metadata = getattr(func, TOOL_ATTR, None)
    if isinstance(metadata, ToolMetadata):
        return metadata.name
    return func.__name__


def get_tool_category(func: Callable[..., Any]) -> str:
    """Get tool category from a decorated function."""
    metadata = getattr(func, TOOL_ATTR, None)
    if isinstance(metadata, ToolMetadata):
        return metadata.category
    return "uncategorized"
