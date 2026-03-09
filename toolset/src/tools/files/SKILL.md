---
name: processing-files
description: File conversion and data extraction tools. Use for PDF to markdown conversion or extracting tables from markdown files to CSV format.
---

# File Processing Tools

Tools for converting and processing file formats.

## PDF to Markdown

Extract text from PDF files and convert to markdown format.

### Basic usage

```python
result = await pdf_to_markdown(file_path="/path/to/document.pdf")
# Returns: {"success": True, "data": {"markdown": "# Document Title\n\nContent..."}}
```

### With page limits

```python
# Extract first 5 pages only
result = await pdf_to_markdown(
    file_path="/path/to/document.pdf",
    max_pages=5
)
```

### Response format

```json
{
  "success": true,
  "data": {
    "markdown": "extracted markdown content",
    "page_count": 10,
    "file_path": "/path/to/document.pdf"
  }
}
```

## Markdown Table Extraction

Extract tables from markdown content and convert to CSV format.

### Extract tables from markdown string

```python
markdown = """
| Name | Age |
|------|-----|
| Alice | 30 |
| Bob | 25 |
"""
# Extract all tables
result = await markdown_extract_tables(markdown_content=markdown)

# Extract a specific table by index (0-based)
result = await markdown_extract_tables(markdown_content=markdown, table_index=0)
```

### Response format

```json
{
  "success": true,
  "data": {
    "tables": [
      {
        "index": 0,
        "rows": 3,
        "columns": 2,
        "csv": "Name,Age\nAlice,30\nBob,25\n"
      }
    ],
    "count": 1
  }
}
```

## When to use

- Converting PDF reports to readable text
- Extracting content from PDF documents
- Extracting data tables from markdown for analysis
- Converting markdown tables to spreadsheet-compatible CSV format
