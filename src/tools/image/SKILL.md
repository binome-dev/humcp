---
name: image-tools
description: Image processing tools including OCR text extraction. Use when you need to extract text from images.
---

# Image Tools

Tools for processing and extracting data from images.

## Text Extraction (OCR)

Extract text from images using Tesseract OCR and output as markdown.

### Basic usage

```python
# Extract text from base64 encoded image
result = await image_extract_text(image_data="iVBORw0KGgo...")
```

### With data URL

```python
# Also accepts data URL format
result = await image_extract_text(
    image_data="data:image/png;base64,iVBORw0KGgo..."
)
```

### With language

```python
# Extract Chinese text
result = await image_extract_text(
    image_data="...",
    language="chi_sim"
)

# Extract Japanese text
result = await image_extract_text(
    image_data="...",
    language="jpn"
)
```

### Response format

```json
{
  "success": true,
  "data": {
    "markdown": "Extracted text content\n\nFormatted as markdown"
  }
}
```

## Supported Languages

Common language codes:
- `eng` - English (default)
- `chi_sim` - Chinese Simplified
- `chi_tra` - Chinese Traditional
- `jpn` - Japanese
- `kor` - Korean
- `fra` - French
- `deu` - German
- `spa` - Spanish

## Requirements

- Tesseract OCR must be installed on the system
- Additional language packs may need to be installed for non-English text

## When to use

- Extract text from screenshots
- Digitize scanned documents
- Process images containing text for analysis
- Convert image-based content to searchable text
