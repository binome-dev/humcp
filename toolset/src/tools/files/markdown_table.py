"""Markdown table extraction tool."""

from __future__ import annotations

import csv
import io
import logging
import re

from src.humcp.decorator import tool
from src.tools.files.schemas import (
    ExtractedTable,
    MarkdownExtractTablesData,
    MarkdownExtractTablesResponse,
)

logger = logging.getLogger("humcp.tools.files.markdown_table")


def _parse_markdown_table(table_text: str) -> list[list[str]]:
    """Parse a markdown table into rows of cells.

    Args:
        table_text: Markdown table text.

    Returns:
        List of rows, each row is a list of cell values.
    """
    lines = table_text.strip().split("\n")
    rows: list[list[str]] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip separator lines (e.g., |---|---|)
        if re.match(r"^\|[\s\-:|\+]+\|$", line):
            continue

        # Parse cells from pipe-separated line
        if line.startswith("|") and line.endswith("|"):
            # Remove leading/trailing pipes and split
            cells = line[1:-1].split("|")
            cells = [cell.strip() for cell in cells]
            if cells:
                rows.append(cells)

    return rows


def _extract_tables_from_markdown(content: str) -> list[list[list[str]]]:
    """Extract all tables from markdown content.

    Args:
        content: Full markdown content.

    Returns:
        List of tables, each table is a list of rows.
    """
    tables: list[list[list[str]]] = []

    # Pattern to match markdown tables
    # A table starts with a line containing |, followed by a separator line with -
    table_pattern = re.compile(
        r"(\|[^\n]+\|\n\|[\s\-:|\+]+\|\n(?:\|[^\n]+\|\n?)*)",
        re.MULTILINE,
    )

    matches = table_pattern.findall(content)

    for match in matches:
        parsed = _parse_markdown_table(match)
        if parsed:
            tables.append(parsed)

    return tables


def _table_to_csv(table: list[list[str]]) -> str:
    """Convert a parsed table to CSV format.

    Args:
        table: List of rows, each row is a list of cell values.

    Returns:
        CSV formatted string.
    """
    output = io.StringIO(newline="")
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

    for row in table:
        writer.writerow(row)

    return output.getvalue()


@tool()
async def markdown_extract_tables(
    markdown_content: str,
    table_index: int | None = None,
) -> MarkdownExtractTablesResponse:
    """Extract tables from markdown content and convert to CSV format.

    Parses markdown tables (pipe-separated format) and outputs CSV strings.

    Args:
        markdown_content: Markdown content containing table(s).
        table_index: Optional index of specific table to extract (0-based).
                    If not provided, extracts all tables.

    Returns:
        Success status with CSV data for extracted tables.

    Example:
        markdown = '''
        | Name | Age |
        |------|-----|
        | Alice | 30 |
        | Bob | 25 |
        '''
        # Extract all tables
        result = await markdown_extract_tables(markdown_content=markdown)

        # Extract only the first table
        result = await markdown_extract_tables(markdown_content=markdown, table_index=0)
    """
    try:
        tables = _extract_tables_from_markdown(markdown_content)

        if not tables:
            return MarkdownExtractTablesResponse(
                success=True,
                data=MarkdownExtractTablesData(
                    tables=[],
                    count=0,
                    message="No tables found in content",
                ),
            )

        # Extract specific table or all tables
        if table_index is not None:
            if table_index < 0 or table_index >= len(tables):
                return MarkdownExtractTablesResponse(
                    success=False,
                    error=f"Table index {table_index} out of range. "
                    f"Content contains {len(tables)} table(s).",
                )
            selected_tables = [tables[table_index]]
            indices = [table_index]
        else:
            selected_tables = tables
            indices = list(range(len(tables)))

        # Convert to CSV
        results = []
        for idx, table in zip(indices, selected_tables, strict=False):
            csv_data = _table_to_csv(table)
            results.append(
                ExtractedTable(
                    index=idx,
                    rows=len(table),
                    columns=len(table[0]) if table else 0,
                    csv=csv_data,
                )
            )

        logger.info("Extracted %d table(s) from markdown content", len(results))

        return MarkdownExtractTablesResponse(
            success=True,
            data=MarkdownExtractTablesData(
                tables=results,
                count=len(results),
            ),
        )

    except Exception as e:
        logger.exception("Failed to extract tables from markdown")
        return MarkdownExtractTablesResponse(success=False, error=str(e))
