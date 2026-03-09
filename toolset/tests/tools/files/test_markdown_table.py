"""Tests for markdown table extraction tools."""

import pytest
from src.tools.files.markdown_table import (
    _extract_tables_from_markdown,
    _parse_markdown_table,
    _table_to_csv,
    markdown_extract_tables,
)


class TestParseMarkdownTable:
    """Tests for _parse_markdown_table."""

    def test_simple_table(self):
        """Should parse a simple table."""
        table = """
| Name | Age |
|------|-----|
| Alice | 30 |
| Bob | 25 |
"""
        result = _parse_markdown_table(table)
        assert len(result) == 3
        assert result[0] == ["Name", "Age"]
        assert result[1] == ["Alice", "30"]
        assert result[2] == ["Bob", "25"]

    def test_table_with_alignment(self):
        """Should handle alignment markers in separator."""
        table = """
| Left | Center | Right |
|:-----|:------:|------:|
| A | B | C |
"""
        result = _parse_markdown_table(table)
        assert len(result) == 2
        assert result[0] == ["Left", "Center", "Right"]
        assert result[1] == ["A", "B", "C"]

    def test_empty_cells(self):
        """Should handle empty cells."""
        table = """
| A | B | C |
|---|---|---|
| 1 |   | 3 |
"""
        result = _parse_markdown_table(table)
        assert result[1] == ["1", "", "3"]


class TestExtractTablesFromMarkdown:
    """Tests for _extract_tables_from_markdown."""

    def test_single_table(self):
        """Should extract a single table."""
        content = """
# Heading

Some text here.

| Col1 | Col2 |
|------|------|
| A | B |

More text.
"""
        tables = _extract_tables_from_markdown(content)
        assert len(tables) == 1
        assert tables[0][0] == ["Col1", "Col2"]

    def test_multiple_tables(self):
        """Should extract multiple tables."""
        content = """
# First Table

| A | B |
|---|---|
| 1 | 2 |

# Second Table

| X | Y | Z |
|---|---|---|
| a | b | c |
"""
        tables = _extract_tables_from_markdown(content)
        assert len(tables) == 2
        assert len(tables[0][0]) == 2  # First table has 2 columns
        assert len(tables[1][0]) == 3  # Second table has 3 columns

    def test_no_tables(self):
        """Should return empty list when no tables."""
        content = """
# Just some markdown

No tables here!
"""
        tables = _extract_tables_from_markdown(content)
        assert tables == []


class TestTableToCsv:
    """Tests for _table_to_csv."""

    def test_simple_conversion(self):
        """Should convert table to CSV."""
        table = [
            ["Name", "Age"],
            ["Alice", "30"],
            ["Bob", "25"],
        ]
        csv = _table_to_csv(table)
        lines = csv.strip().split("\n")
        assert len(lines) == 3
        assert lines[0] == "Name,Age"
        assert lines[1] == "Alice,30"

    def test_values_with_commas(self):
        """Should properly quote values with commas."""
        table = [
            ["Name", "Description"],
            ["Item", "First, Second"],
        ]
        csv = _table_to_csv(table)
        assert '"First, Second"' in csv

    def test_empty_table(self):
        """Should handle empty table."""
        csv = _table_to_csv([])
        assert csv == ""


class TestMarkdownExtractTables:
    """Tests for markdown_extract_tables tool."""

    @pytest.mark.asyncio
    async def test_extract_all_tables(self):
        """Should extract all tables from markdown content."""
        markdown = """
# Test Document

| Name | Value |
|------|-------|
| foo | 1 |
| bar | 2 |

Some text.

| A | B | C |
|---|---|---|
| x | y | z |
"""
        result = await markdown_extract_tables(markdown_content=markdown)

        assert result.success is True
        assert result.data.count == 2
        assert "Name,Value" in result.data.tables[0].csv
        assert result.data.tables[1].columns == 3

    @pytest.mark.asyncio
    async def test_extract_specific_table(self):
        """Should extract specific table by index."""
        markdown = """
| A | B |
|---|---|
| 1 | 2 |

| X | Y | Z |
|---|---|---|
| a | b | c |
"""
        result = await markdown_extract_tables(markdown_content=markdown, table_index=1)

        assert result.success is True
        assert result.data.count == 1
        assert result.data.tables[0].columns == 3
        assert "X,Y,Z" in result.data.tables[0].csv

    @pytest.mark.asyncio
    async def test_no_tables(self):
        """Should handle content with no tables."""
        result = await markdown_extract_tables(
            markdown_content="# Just text\n\nNo tables here."
        )

        assert result.success is True
        assert result.data.count == 0
        assert result.data.tables == []

    @pytest.mark.asyncio
    async def test_invalid_table_index(self):
        """Should return error for invalid table index."""
        markdown = """
| A | B |
|---|---|
| 1 | 2 |
"""
        result = await markdown_extract_tables(markdown_content=markdown, table_index=5)

        assert result.success is False
        assert "out of range" in result.error

    @pytest.mark.asyncio
    async def test_simple_table(self):
        """Should convert simple markdown table to CSV."""
        markdown = """
| Name | Age |
|------|-----|
| Alice | 30 |
| Bob | 25 |
"""
        result = await markdown_extract_tables(markdown_content=markdown)

        assert result.success is True
        assert result.data.count == 1
        assert result.data.tables[0].rows == 3
        assert result.data.tables[0].columns == 2
        assert "Name,Age" in result.data.tables[0].csv
