import logging
from collections.abc import Callable

from fastmcp import FastMCP

mcp = FastMCP("Humcp Server")

logger = logging.getLogger("humcp.server")


def _register_toolset(name: str, loader: Callable[[FastMCP], None]) -> None:
    """Register a toolset and log the result."""
    try:
        loader(mcp)
        logger.info("Registered toolset: %s", name)
    except ImportError as e:
        logger.warning("%s tools not available: %s", name, e)
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to register toolset %s", name)


try:
    from src.tools.data import csv

    _register_toolset("csv", csv.register_tools)
except ImportError as e:
    logger.warning("CSV tools module missing: %s", e)

try:
    from src.tools.data import pandas

    _register_toolset("pandas", pandas.register_tools)
except ImportError as e:
    logger.warning("Pandas tools module missing: %s", e)

try:
    from src.tools.local import calculator

    _register_toolset("calculator", calculator.register_tools)
except ImportError as e:
    logger.warning("Calculator tools module missing: %s", e)

try:
    from src.tools.local import local_file_system

    _register_toolset("local_file_system", local_file_system.register_tools)
except ImportError as e:
    logger.warning("Local File System tools module missing: %s", e)

try:
    from src.tools.local import shell

    _register_toolset("shell", shell.register_tools)
except ImportError as e:
    logger.warning("Shell tools module missing: %s", e)

try:
    from src.tools.search import tavily_tool

    _register_toolset("tavily_tool", tavily_tool.register_tools)
except ImportError as e:
    logger.warning("Tavily search tools module missing: %s", e)


try:
    from src.tools.files import pdf_to_markdown

    _register_toolset("pdf_to_markdown", pdf_to_markdown.register_tools)
except ImportError as e:
    logger.warning("PDF to Markdown tools module missing: %s", e)

try:
    from src.tools.google import gmail

    _register_toolset("gmail", gmail.register_tools)
except ImportError as e:
    logger.warning("Gmail tools module missing: %s", e)

try:
    from src.tools.google import calendar

    _register_toolset("calendar", calendar.register_tools)
except ImportError as e:
    logger.warning("Google Calendar tools module missing: %s", e)

try:
    from src.tools.google import drive

    _register_toolset("drive", drive.register_tools)
except ImportError as e:
    logger.warning("Google Drive tools module missing: %s", e)

try:
    from src.tools.google import tasks

    _register_toolset("tasks", tasks.register_tools)
except ImportError as e:
    logger.warning("Google Tasks tools module missing: %s", e)

try:
    from src.tools.google import docs

    _register_toolset("docs", docs.register_tools)
except ImportError as e:
    logger.warning("Google Docs tools module missing: %s", e)

try:
    from src.tools.google import sheets

    _register_toolset("sheets", sheets.register_tools)
except ImportError as e:
    logger.warning("Google Sheets tools module missing: %s", e)

try:
    from src.tools.google import slides

    _register_toolset("slides", slides.register_tools)
except ImportError as e:
    logger.warning("Google Slides tools module missing: %s", e)

try:
    from src.tools.google import forms

    _register_toolset("forms", forms.register_tools)
except ImportError as e:
    logger.warning("Google Forms tools module missing: %s", e)

try:
    from src.tools.google import chat

    _register_toolset("chat", chat.register_tools)
except ImportError as e:
    logger.warning("Google Chat tools module missing: %s", e)


tool_count = len(getattr(getattr(mcp, "_tool_manager", None), "tools", []))
logger.info("MCP server initialized with %d tools", tool_count)

if __name__ == "__main__":
    logger.info("Starting MCP server on http://0.0.0.0:8081/mcp")
    mcp.run(transport="http", host="0.0.0.0", port=8081)
