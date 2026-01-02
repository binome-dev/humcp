"""Tool modules for HuMCP server.

This package contains tool implementations organized by category:
- data/: Data processing tools (CSV, pandas)
- files/: File format tools
- google/: Google API tools (Sheets, Slides, etc.)
- local/: Local system tools (filesystem, shell)
- search/: Search tools

Tools are auto-discovered at server startup from Python files in this package.
Use the @tool decorator from src.humcp.decorator to register new tools.

Example:
    from src.humcp.decorator import tool

    @tool("my_tool", category="custom")
    async def my_tool(param: str) -> dict:
        '''Tool description.'''
        return {"success": True, "data": param}
"""

from src.humcp.decorator import tool

__all__ = ["tool"]
