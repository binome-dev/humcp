"""Storage interface and implementations for custom tools."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("humcp.builder.storage")


@dataclass
class CustomToolDefinition:
    """Definition of a custom tool."""

    name: str
    description: str
    code: str
    parameters: dict[str, Any]
    category: str = "custom"
    enabled: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "parameters": self.parameters,
            "category": self.category,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ToolStorage(ABC):
    """Abstract interface for tool storage.

    Implement this interface for different storage backends:
    - InMemoryToolStorage (default)
    - SQLiteToolStorage (future)
    - PostgresToolStorage (future)
    """

    @abstractmethod
    async def save(self, tool: CustomToolDefinition) -> None:
        """Save a tool definition."""
        ...

    @abstractmethod
    async def get(self, name: str) -> CustomToolDefinition | None:
        """Get a tool by name."""
        ...

    @abstractmethod
    async def delete(self, name: str) -> bool:
        """Delete a tool by name. Returns True if deleted."""
        ...

    @abstractmethod
    async def list_all(self) -> list[CustomToolDefinition]:
        """List all tools."""
        ...

    @abstractmethod
    async def exists(self, name: str) -> bool:
        """Check if a tool exists."""
        ...

    @abstractmethod
    async def update(self, name: str, **kwargs: Any) -> CustomToolDefinition | None:
        """Update a tool's fields. Returns updated tool or None if not found."""
        ...


class InMemoryToolStorage(ToolStorage):
    """In-memory storage for custom tools.

    Tools are lost on server restart. Use for development/testing.
    """

    def __init__(self) -> None:
        self._tools: dict[str, CustomToolDefinition] = {}

    async def save(self, tool: CustomToolDefinition) -> None:
        """Save a tool definition."""
        self._tools[tool.name] = tool
        logger.info("Tool saved name=%s", tool.name)

    async def get(self, name: str) -> CustomToolDefinition | None:
        """Get a tool by name."""
        return self._tools.get(name)

    async def delete(self, name: str) -> bool:
        """Delete a tool by name."""
        if name in self._tools:
            del self._tools[name]
            logger.info("Tool deleted name=%s", name)
            return True
        return False

    async def list_all(self) -> list[CustomToolDefinition]:
        """List all tools."""
        return list(self._tools.values())

    async def exists(self, name: str) -> bool:
        """Check if a tool exists."""
        return name in self._tools

    async def update(self, name: str, **kwargs: Any) -> CustomToolDefinition | None:
        """Update a tool's fields."""
        tool = self._tools.get(name)
        if tool is None:
            return None

        for key, value in kwargs.items():
            if hasattr(tool, key):
                setattr(tool, key, value)

        tool.updated_at = datetime.now()
        logger.info("Tool updated name=%s fields=%s", name, list(kwargs.keys()))
        return tool

    def clear(self) -> None:
        """Clear all tools (for testing)."""
        self._tools.clear()


# Global storage instance
_storage: ToolStorage | None = None


def get_tool_storage() -> ToolStorage:
    """Get the global tool storage instance."""
    global _storage
    if _storage is None:
        _storage = InMemoryToolStorage()
    return _storage


def set_tool_storage(storage: ToolStorage) -> None:
    """Set a custom tool storage implementation."""
    global _storage
    _storage = storage


def reset_tool_storage() -> None:
    """Reset the global storage (for testing)."""
    global _storage
    _storage = None
