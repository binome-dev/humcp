"""Tests for image OCR tool."""

import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image, ImageDraw
from src.tools.image.ocr import _text_to_markdown, image_extract_text

# Check if Tesseract is installed
TESSERACT_AVAILABLE = shutil.which("tesseract") is not None


def create_test_image_with_text(text: str, size: tuple = (200, 50)) -> str:
    """Create a test image with text and return path to temp file."""
    image = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), text, fill="black")

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    image.save(temp_file.name, format="PNG")

    return temp_file.name


class TestTextToMarkdown:
    """Tests for _text_to_markdown."""

    def test_simple_text(self):
        """Should convert simple text."""
        text = "Hello World"
        result = _text_to_markdown(text)
        assert result == "Hello World"

    def test_multiline_text(self):
        """Should preserve multiline text."""
        text = "Line 1\nLine 2\nLine 3"
        result = _text_to_markdown(text)
        assert result == "Line 1\nLine 2\nLine 3"

    def test_text_with_whitespace(self):
        """Should handle whitespace."""
        text = "  Hello  \n  World  "
        result = _text_to_markdown(text)
        assert "Hello" in result
        assert "World" in result

    def test_empty_text(self):
        """Should handle empty text."""
        result = _text_to_markdown("")
        assert result == ""


class TestImageExtractText:
    """Tests for image_extract_text tool."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
    async def test_extract_text_success(self):
        """Should extract text from image."""
        # Create image with text
        file_path = create_test_image_with_text("Hello")

        try:
            result = await image_extract_text(file_path=file_path)

            assert result.success is True
            assert result.data.markdown is not None
        finally:
            Path(file_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
    async def test_empty_image(self):
        """Should handle image with no text."""
        # Create blank image
        image = Image.new("RGB", (100, 100), color="white")
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        image.save(temp_file.name, format="PNG")

        try:
            result = await image_extract_text(file_path=temp_file.name)

            assert result.success is True
            # May or may not detect text in blank image
        finally:
            Path(temp_file.name).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_file_not_found(self):
        """Should return error for non-existent file."""
        result = await image_extract_text(file_path="/nonexistent/path/image.png")

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    @pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
    async def test_with_language_parameter(self):
        """Should accept language parameter."""
        file_path = create_test_image_with_text("Hello")

        try:
            result = await image_extract_text(file_path=file_path, language="eng")

            assert result.success is True
        finally:
            Path(file_path).unlink(missing_ok=True)
