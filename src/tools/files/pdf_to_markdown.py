from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP

try:
    from markitdown import MarkItDown
except ImportError:
    raise ImportError(
        "markitdown is required for PDF to Markdown conversion. Install with: pip install 'markitdown[all]'"
    )


async def convert_to_markdown(pdf_path: str) -> str:
    """
    Convert a PDF file to Markdown format.

    Args:
        pdf_path: Path to the PDF file to convert.

    Returns:
        Success flag and markdown content or error message.
    """
    try:
        # Validate that the PDF file exists
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            return {"success": False, "error": f"PDF file not found: {pdf_path}"}

        if not pdf_file.suffix.lower() == ".pdf":
            return {"success": False, "error": f"File is not a PDF: {pdf_path}"}

        # Convert PDF to markdown
        md = MarkItDown()
        result = md.convert(str(pdf_file))

        markdown_content = (
            result.text_content if hasattr(result, "text_content") else str(result)
        )

        return markdown_content

    except Exception as e:
        raise e


def register_tools(mcp: FastMCP) -> None:
    """Register PDF to Markdown conversion tool with the MCP server."""
    mcp.tool(name="files/convert_to_markdown")(convert_to_markdown)
