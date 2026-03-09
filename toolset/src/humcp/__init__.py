"""HuMCP - Human-friendly MCP server with FastAPI adapter.

Public API:
    tool: Decorator to mark functions as MCP tools
    create_app: Create FastAPI app with REST and MCP endpoints
    RegisteredTool: Type for registered tool (for type hints)
"""

from src.humcp.decorator import RegisteredTool, tool
from src.humcp.server import create_app

__all__ = ["tool", "create_app", "RegisteredTool"]
