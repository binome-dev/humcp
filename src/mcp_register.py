import importlib.util
import logging
from collections.abc import Callable
from pathlib import Path

from fastmcp import FastMCP

from src.tools import TOOL_REGISTRY, ToolRegistration

logger = logging.getLogger("humcp.server")

TOOLS_DIR = Path(__file__).parent / "tools"


def _register_tool(mcp_instance: FastMCP, registration: ToolRegistration) -> None:
    """Register a single tool and log the result."""

    try:
        mcp_instance.tool(name=registration.name)(registration.func)
        logger.info(
            "Registered tool: %s (category=%s)",
            registration.name,
            registration.category,
        )
    except ImportError as e:
        logger.warning("%s tool not available: %s", registration.name, e)
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to register tool %s", registration.name)


def _import_tool_modules() -> None:
    """Import all tool modules so their @tool decorators run.

    Scans the tools directory for .py files directly, without requiring __init__.py.
    """

    for py_file in TOOLS_DIR.rglob("*.py"):
        if py_file.name.startswith("_"):
            continue

        # Convert path to module name: src/tools/local/calculator.py -> src.tools.local.calculator
        relative_path = py_file.relative_to(TOOLS_DIR.parent.parent)
        module_name = str(relative_path.with_suffix("")).replace("/", ".")

        try:
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.debug("Imported tool module: %s", module_name)
        except ImportError as e:
            logger.warning("Tool module %s missing dependency: %s", module_name, e)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Failed to import tool module %s", module_name)


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server with all available tools."""

    mcp = FastMCP("Humcp Server")
    logger.info("Creating MCP server")

    _import_tool_modules()

    seen_funcs: set[Callable[..., object]] = set()
    for registration in TOOL_REGISTRY:
        if registration.func in seen_funcs:
            logger.debug("Skipping duplicate tool: %s", registration.name)
            continue
        seen_funcs.add(registration.func)
        _register_tool(mcp, registration)

    tool_count = len(getattr(getattr(mcp, "_tool_manager", None), "tools", []))
    logger.info("MCP server initialized with %d tools", tool_count)

    return mcp
