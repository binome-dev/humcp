from __future__ import annotations

import logging
from pathlib import Path

from src.humcp.decorator import tool
from src.humcp.permissions import check_permission, require_auth
from src.humcp.storage_path import is_storage_path, parse_storage_path, resolve_path
from src.tools.files.schemas import ConvertToMarkdownData, ConvertToMarkdownResponse

try:
    from markitdown import MarkItDown
except ImportError as err:
    raise ImportError(
        "markitdown is required for PDF to Markdown conversion. Install with: pip install 'markitdown[all]'"
    ) from err

logger = logging.getLogger("humcp.tools.pdf_to_markdown")


@tool()
async def convert_to_markdown(pdf_path: str) -> ConvertToMarkdownResponse:
    """
    Convert a PDF file to Markdown format.

    Supports both local file paths and storage URLs (minio://bucket/path).

    Args:
        pdf_path: Path to the PDF file (local path or minio:// URL).

    Returns:
        Success flag and markdown content or error message.
    """
    try:
        # Permission check: storage path -> check bucket permission, else require auth
        if is_storage_path(pdf_path):
            bucket, _ = parse_storage_path(pdf_path)
            await check_permission("storage_bucket", bucket, "viewer")
        else:
            await require_auth()

        # Use resolve_path to handle both local and minio:// paths
        async with resolve_path(pdf_path) as local_path:
            pdf_file = Path(local_path)
            if not pdf_file.exists():
                return ConvertToMarkdownResponse(
                    success=False, error=f"PDF file not found: {pdf_path}"
                )

            if pdf_file.suffix.lower() != ".pdf":
                return ConvertToMarkdownResponse(
                    success=False, error=f"File is not a PDF: {pdf_path}"
                )

            md = MarkItDown()
            logger.info("Converting PDF to markdown path=%s", pdf_file)
            result = md.convert(str(pdf_file))

            markdown_content = (
                result.text_content if hasattr(result, "text_content") else str(result)
            )

            logger.info("PDF conversion complete path=%s", pdf_file)
            return ConvertToMarkdownResponse(
                success=True, data=ConvertToMarkdownData(markdown=markdown_content)
            )
    except Exception as e:
        logger.exception("Failed to convert PDF to markdown")
        return ConvertToMarkdownResponse(success=False, error=str(e))
