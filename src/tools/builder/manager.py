"""Manager for dynamic custom tool registration with MCP and REST."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.tools.builder.sandbox import compile_code, execute_sandboxed
from src.tools.builder.storage import CustomToolDefinition, get_tool_storage

if TYPE_CHECKING:
    from fastapi import FastAPI
    from fastmcp import FastMCP

logger = logging.getLogger("humcp.builder.manager")


class CustomToolManager:
    """Manages dynamic registration of custom tools with MCP and REST.

    This manager allows custom tools to be registered and unregistered
    at runtime, making them available as first-class MCP/REST tools.
    """

    _instance: CustomToolManager | None = None
    _initialized: bool = False

    def __new__(cls) -> CustomToolManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if CustomToolManager._initialized:
            return
        self._mcp: FastMCP | None = None
        self._app: FastAPI | None = None
        self._registered_tools: dict[str, Any] = {}
        self._compiled_cache: dict[str, Any] = {}
        CustomToolManager._initialized = True

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (for testing)."""
        cls._instance = None
        cls._initialized = False

    def initialize(self, mcp: FastMCP, app: FastAPI) -> None:
        """Initialize with MCP and FastAPI instances."""
        self._mcp = mcp
        self._app = app
        logger.info("CustomToolManager initialized")

    def is_initialized(self) -> bool:
        """Check if manager is initialized."""
        return self._mcp is not None and self._app is not None

    async def register_tool(self, tool_def: CustomToolDefinition) -> bool:
        """Register a custom tool with MCP.

        Args:
            tool_def: The custom tool definition.

        Returns:
            True if registration succeeded.
        """
        if not self.is_initialized():
            logger.warning("CustomToolManager not initialized")
            return False

        if tool_def.name in self._registered_tools:
            logger.warning("Tool already registered name=%s", tool_def.name)
            return False

        try:
            # Compile the code
            compiled = compile_code(tool_def.code)
            self._compiled_cache[tool_def.name] = compiled

            # Create wrapper function
            async def tool_wrapper(
                _name: str = tool_def.name,
                _compiled: Any = compiled,
                **kwargs: Any,
            ) -> dict[str, Any]:
                """Dynamic wrapper for custom tool execution."""
                try:
                    result = await execute_sandboxed(
                        compiled_code=_compiled,
                        function_name="execute",
                        params=kwargs,
                    )
                    return result
                except Exception as e:
                    return {"success": False, "error": str(e)}

            # Set function metadata for FastMCP
            tool_wrapper.__name__ = tool_def.name
            tool_wrapper.__doc__ = tool_def.description

            # Register with FastMCP
            if self._mcp:
                self._mcp.tool(name=tool_def.name)(tool_wrapper)
                self._registered_tools[tool_def.name] = tool_wrapper
                logger.info("Custom tool registered with MCP name=%s", tool_def.name)

            return True

        except Exception:
            logger.exception("Failed to register custom tool name=%s", tool_def.name)
            return False

    async def unregister_tool(self, name: str) -> bool:
        """Unregister a custom tool from MCP.

        Note: FastMCP doesn't support removing tools at runtime,
        so we just remove from our tracking.

        Args:
            name: Name of the tool to unregister.

        Returns:
            True if unregistration succeeded.
        """
        if name not in self._registered_tools:
            return False

        del self._registered_tools[name]
        if name in self._compiled_cache:
            del self._compiled_cache[name]

        logger.info("Custom tool unregistered name=%s", name)
        return True

    def is_registered(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._registered_tools

    def list_registered(self) -> list[str]:
        """List all registered custom tool names."""
        return list(self._registered_tools.keys())

    async def sync_enabled_tools(self) -> int:
        """Sync all enabled tools from storage to MCP.

        Call this during server startup to register all enabled custom tools.

        Returns:
            Number of tools registered.
        """
        storage = get_tool_storage()
        tools = await storage.list_all()

        count = 0
        for tool_def in tools:
            if tool_def.enabled and not self.is_registered(tool_def.name):
                if await self.register_tool(tool_def):
                    count += 1

        logger.info("Synced %d enabled custom tools", count)
        return count


# Global manager instance
_manager: CustomToolManager | None = None


def get_custom_tool_manager() -> CustomToolManager:
    """Get the global CustomToolManager instance."""
    global _manager
    if _manager is None:
        _manager = CustomToolManager()
    return _manager


def reset_custom_tool_manager() -> None:
    """Reset the global manager (for testing)."""
    global _manager
    CustomToolManager.reset()
    _manager = None
