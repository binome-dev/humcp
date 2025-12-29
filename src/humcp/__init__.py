"""HuMCP - Simple MCP + REST server for tools.

Usage:
    from humcp import tool, create_app

    @tool("calculator_add")
    async def add(a: float, b: float) -> dict:
        return {"success": True, "data": {"result": a + b}}

    app = create_app()
"""

from .decorator import TOOL_REGISTRY, ToolRegistration, tool
from .server import create_app

__all__ = ["tool", "create_app", "TOOL_REGISTRY", "ToolRegistration"]
