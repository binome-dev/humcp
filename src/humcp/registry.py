"""Tool registry - stores all registered tools."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

__all__ = ["ToolRegistration", "TOOL_REGISTRY"]


@dataclass(frozen=True)
class ToolRegistration:
    """A registered tool."""

    name: str
    category: str
    func: Callable[..., Any]


TOOL_REGISTRY: list[ToolRegistration] = []
_TOOL_NAMES: set[str] = set()
