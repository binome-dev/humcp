"""Image text extraction (OCR) tool."""

from __future__ import annotations

import logging
from pathlib import Path

import pytesseract
from PIL import Image

from src.humcp.decorator import tool
from src.humcp.storage_path import resolve_path
from src.tools.image.schemas import ImageExtractTextData, ImageExtractTextResponse

logger = logging.getLogger("humcp.tools.image.ocr")


def _text_to_markdown(text: str) -> str:
    """Convert extracted text to markdown format.

    Args:
        text: Raw extracted text.

    Returns:
        Markdown formatted text.
    """
    lines = text.strip().split("\n")
    markdown_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            markdown_lines.append("")
            continue

        # Preserve the line as-is in markdown
        markdown_lines.append(line)

    return "\n".join(markdown_lines)


@tool()
async def image_extract_text(
    file_path: str,
    language: str = "eng",
) -> ImageExtractTextResponse:
    """Extract text from an image using OCR and output as markdown.

    Uses Tesseract OCR to extract text from images. Supports multiple languages.
    Supports both local file paths and storage URLs (minio://bucket/path).

    Args:
        file_path: Path to the image file (local path or minio:// URL).
        language: Language code for OCR (default: "eng" for English).
                 Common codes: eng, chi_sim (Chinese Simplified), chi_tra (Chinese Traditional),
                 jpn (Japanese), kor (Korean), fra (French), deu (German), spa (Spanish).

    Returns:
        Success status with extracted text in markdown format.

    Example:
        # Extract text from local image file
        result = await image_extract_text(file_path="/path/to/image.png")

        # Extract text from storage file
        result = await image_extract_text(file_path="minio://bucket/path/to/image.png")

        # Extract Chinese text
        result = await image_extract_text(file_path="/path/to/image.png", language="chi_sim")
    """
    try:
        # Use resolve_path to handle both local and minio:// paths
        async with resolve_path(file_path) as local_path:
            path = Path(local_path)
            if not path.exists():
                return ImageExtractTextResponse(
                    success=False, error=f"File not found: {file_path}"
                )

            # Open image from file
            image = Image.open(path)

            # Extract text using Tesseract
            raw_text = pytesseract.image_to_string(image, lang=language)

            if not raw_text.strip():
                return ImageExtractTextResponse(
                    success=True,
                    data=ImageExtractTextData(
                        markdown="",
                        message="No text found in image",
                    ),
                )

            # Convert to markdown format
            markdown_text = _text_to_markdown(raw_text)

            logger.info("Extracted %d characters from image", len(markdown_text))

            return ImageExtractTextResponse(
                success=True,
                data=ImageExtractTextData(
                    markdown=markdown_text,
                ),
            )

    except Exception as e:
        logger.exception("Failed to extract text from image")
        return ImageExtractTextResponse(success=False, error=str(e))
