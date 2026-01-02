"""Tool registry - stores all registered tools.

This module provides the global registry for MCP tools. Tools are registered
at module import time using the @tool decorator from the decorator module.

Thread Safety:
    TOOL_REGISTRY and _TOOL_NAMES are module-level globals that are populated
    at import time. They are safe for concurrent reads after server startup.
    Dynamic tool registration during runtime is not thread-safe and should
    be avoided in production.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

__all__ = ["ToolRegistration", "TOOL_REGISTRY", "_TOOL_NAMES"]


@dataclass(frozen=True)
class ToolRegistration:
    """A registered tool.

    Attributes:
        name: Unique identifier for the tool.
        category: Category grouping (e.g., 'google', 'local', 'data').
        func: The async function that implements the tool.
    """

    name: str
    category: str
    func: Callable[..., Any]


# Global registry populated at import time by @tool decorators
TOOL_REGISTRY: list[ToolRegistration] = []
_TOOL_NAMES: set[str] = set()
