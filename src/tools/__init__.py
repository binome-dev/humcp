from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastmcp import FastMCP


@dataclass(frozen=True)
class ToolRegistration:
    """Represents a single MCP tool discovered via decorator."""

    name: str
    category: str
    func: Callable[..., Any]


# Registry of tool registrations discovered via @tool decorator.
TOOL_REGISTRY: list[ToolRegistration] = []


def tool(
    name: str | None = None, category: str | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to mark a function as an MCP tool for auto-registration."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or func.__name__
        tool_category = category or func.__module__.split(".")[-1]
        TOOL_REGISTRY.append(ToolRegistration(tool_name, tool_category, func))
        return func

    return decorator
