---
name: academic-research
description: Search and retrieve academic papers and knowledge articles from arXiv, PubMed, and Wikipedia. Use when the user needs scientific papers, biomedical research, or encyclopedic knowledge.
---

# Research Tools

Tools for searching academic databases and knowledge sources.

## arXiv Tools

Search and read academic papers from arXiv.

### Requirements

No API key required. Install packages:
- `arxiv`
- `pypdf` (for reading paper PDFs)

### Search Papers

```python
result = await arxiv_search(
    query="transformer attention mechanism",
    max_results=5
)
```

### Read Paper Content

```python
result = await arxiv_read_paper(
    paper_ids=["2103.03404v1", "2301.07041v2"],
    pages_to_read=5
)
```

## PubMed Tools

Search biomedical and life sciences literature.

### Requirements

No API key required (optional: `NCBI_API_KEY` for higher rate limits).

### Search Articles

```python
result = await pubmed_search(
    query="CRISPR gene therapy",
    max_results=10
)
```

### Get Article by PMID

```python
result = await pubmed_get_article(pmid="12345678")
```

## Wikipedia Tools

Search and retrieve Wikipedia articles.

### Requirements

No API key required. Install package: `wikipedia`

### Search Wikipedia

```python
result = await wikipedia_search(
    query="quantum computing",
    max_results=5
)
```

### Get Full Page

```python
result = await wikipedia_get_page(title="Quantum computing")
```

### Response Format

All tools return:

```json
{
  "success": true,
  "data": { ... }
}
```

## When to Use

- Searching for academic or scientific papers
- Looking up biomedical research and clinical studies
- Finding encyclopedic knowledge on any topic
- Getting abstracts, summaries, and full-text content
- Citing sources with DOIs and URLs
