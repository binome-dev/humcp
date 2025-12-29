"""Tool decorator and registry."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

__all__ = ["tool", "TOOL_REGISTRY", "ToolRegistration"]


@dataclass(frozen=True)
class ToolRegistration:
    """A registered tool."""

    name: str
    category: str
    func: Callable[..., Any]


TOOL_REGISTRY: list[ToolRegistration] = []


def tool(
    name: str | None = None, category: str | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to register a function as an MCP tool.

    Args:
        name: Tool name. Defaults to function name.
        category: Tool category. Defaults to module's last path component.

    Example:
        @tool("calculator_add")
        async def add(a: float, b: float) -> dict:
            return {"success": True, "data": {"result": a + b}}
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or func.__name__
        tool_category = category or func.__module__.split(".")[-1]
        TOOL_REGISTRY.append(ToolRegistration(tool_name, tool_category, func))
        return func

    return decorator
