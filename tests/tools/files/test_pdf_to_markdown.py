from unittest.mock import MagicMock, patch

import pytest

from src.tools.files.pdf_to_markdown import convert_to_markdown


@pytest.fixture
def sample_pdf(tmp_path):
    pdf_file = tmp_path / "sample.pdf"
    # Create a minimal PDF-like file (just for path testing)
    pdf_file.write_bytes(b"%PDF-1.4 minimal pdf content")
    return pdf_file


@pytest.fixture
def mock_markitdown():
    with patch("src.tools.files.pdf_to_markdown.MarkItDown") as mock:
        yield mock


class TestConvertToMarkdown:
    @pytest.mark.asyncio
    async def test_convert_success(self, sample_pdf, mock_markitdown):
        mock_result = MagicMock()
        mock_result.text_content = (
            "# Converted Document\n\nThis is the markdown content."
        )
        mock_markitdown.return_value.convert.return_value = mock_result

        result = await convert_to_markdown(str(sample_pdf))
        assert result["success"] is True
        assert "markdown" in result["data"]
        assert "# Converted Document" in result["data"]["markdown"]

    @pytest.mark.asyncio
    async def test_convert_success_without_text_content_attr(
        self, sample_pdf, mock_markitdown
    ):
        # Test when result doesn't have text_content attribute (uses str() fallback)
        class ResultWithoutTextContent:
            def __str__(self):
                return "Fallback string content"

        mock_markitdown.return_value.convert.return_value = ResultWithoutTextContent()

        result = await convert_to_markdown(str(sample_pdf))
        assert result["success"] is True
        assert result["data"]["markdown"] == "Fallback string content"

    @pytest.mark.asyncio
    async def test_convert_file_not_found(self, tmp_path):
        nonexistent_path = str(tmp_path / "nonexistent.pdf")

        result = await convert_to_markdown(nonexistent_path)
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_convert_not_a_pdf(self, tmp_path):
        txt_file = tmp_path / "document.txt"
        txt_file.write_text("This is a text file")

        result = await convert_to_markdown(str(txt_file))
        assert result["success"] is False
        assert "not a pdf" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_convert_wrong_extension(self, tmp_path):
        doc_file = tmp_path / "document.docx"
        doc_file.write_bytes(b"fake docx content")

        result = await convert_to_markdown(str(doc_file))
        assert result["success"] is False
        assert "not a pdf" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_convert_exception(self, sample_pdf, mock_markitdown):
        mock_markitdown.return_value.convert.side_effect = Exception(
            "Conversion failed: corrupted PDF"
        )

        result = await convert_to_markdown(str(sample_pdf))
        assert result["success"] is False
        assert "corrupted PDF" in result["error"]

    @pytest.mark.asyncio
    async def test_convert_empty_pdf(self, sample_pdf, mock_markitdown):
        mock_result = MagicMock()
        mock_result.text_content = ""
        mock_markitdown.return_value.convert.return_value = mock_result

        result = await convert_to_markdown(str(sample_pdf))
        assert result["success"] is True
        assert result["data"]["markdown"] == ""

    @pytest.mark.asyncio
    async def test_convert_complex_markdown(self, sample_pdf, mock_markitdown):
        complex_markdown = """# Document Title

        ## Section 1

        This is a paragraph with **bold** and *italic* text.

        ### Subsection 1.1

        - Item 1
        - Item 2
        - Item 3

        ## Section 2

        | Column A | Column B |
        |----------|----------|
        | Value 1  | Value 2  |
        """
        mock_result = MagicMock()
        mock_result.text_content = complex_markdown
        mock_markitdown.return_value.convert.return_value = mock_result

        result = await convert_to_markdown(str(sample_pdf))
        assert result["success"] is True
        assert "# Document Title" in result["data"]["markdown"]
        assert "| Column A |" in result["data"]["markdown"]
