---
name: web-scraping-crawling
description: Scrape, crawl, and extract content from web pages. Use when the user needs to extract text, articles, or structured data from websites, or crawl multiple pages from a site.
---

# Web Scraping & Crawling Tools

Tools for scraping individual pages, crawling entire websites, and extracting structured data.

## Free Tools (No API Key)

### Crawl4AI - Browser-based scraping

```python
result = await crawl4ai_scrape(
    url="https://example.com",
    extract_markdown=True,
    max_length=5000
)
```

### newspaper4k - Article extraction

```python
result = await newspaper_extract(
    url="https://example.com/article",
    max_length=10000
)
```

### trafilatura - Content extraction

```python
result = await trafilatura_extract(
    url="https://example.com",
    include_comments=False,
    output_format="txt"  # or "markdown", "json", "xml"
)
```

## API-Powered Tools

### Firecrawl (FIRECRAWL_API_KEY)

```python
# Single page
result = await firecrawl_scrape(url="https://example.com")

# Multi-page crawl
result = await firecrawl_crawl(url="https://example.com", limit=10)
```

### Spider (SPIDER_API_KEY)

```python
# Single page
result = await spider_scrape(url="https://example.com")

# Multi-page crawl
result = await spider_crawl(url="https://example.com", limit=10)
```

### Jina Reader (JINA_API_KEY optional)

```python
# Read a URL
result = await jina_reader(url="https://example.com")

# Web search
result = await jina_search(query="latest AI news")
```

### ScrapeGraph (SGAI_API_KEY)

```python
# AI-powered structured extraction
result = await scrapegraph_scrape(
    url="https://example.com",
    prompt="Extract all product names and prices"
)

# Convert page to markdown
result = await scrapegraph_markdownify(url="https://example.com")
```

### AgentQL (AGENTQL_API_KEY)

```python
result = await agentql_query(
    url="https://example.com",
    query='{ text_content[] }'
)
```

### Browserbase (BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID)

```python
result = await browserbase_scrape(url="https://example.com")
```

### BrightData (BRIGHTDATA_API_KEY)

```python
result = await brightdata_scrape(url="https://example.com")
```

### Oxylabs (OXYLABS_USERNAME, OXYLABS_PASSWORD)

```python
result = await oxylabs_scrape(
    url="https://example.com",
    source="universal",
    render_javascript=False
)
```

### Linkup (LINKUP_API_KEY)

```python
result = await linkup_search(
    query="machine learning tutorials",
    depth="standard"  # or "deep"
)
```

### Apify (APIFY_API_TOKEN)

```python
result = await apify_run_actor(
    actor_id="apify/web-scraper",
    input_data={"startUrls": [{"url": "https://example.com"}]}
)
```

## Response Format

All tools return a consistent response:

```json
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "title": "Page Title",
    "content": "Extracted text content...",
    "markdown": "# Markdown content...",
    "metadata": {"authors": ["..."], "publish_date": "..."}
  }
}
```

Crawl tools return multiple pages:

```json
{
  "success": true,
  "data": {
    "pages": [
      {"url": "...", "title": "...", "content": "..."}
    ],
    "total_pages": 5
  }
}
```

## When to Use

| Need | Tool |
|------|------|
| Simple article text | `newspaper_extract` |
| Clean main content | `trafilatura_extract` |
| JavaScript-heavy pages | `crawl4ai_scrape`, `browserbase_scrape` |
| Multi-page crawl | `firecrawl_crawl`, `spider_crawl` |
| Structured data extraction | `scrapegraph_scrape`, `agentql_query` |
| Bypass anti-bot protection | `brightdata_scrape`, `oxylabs_scrape` |
| Web search | `jina_search`, `linkup_search` |
| Pre-built scraper workflows | `apify_run_actor` |
| Page to markdown | `firecrawl_scrape`, `scrapegraph_markdownify`, `jina_reader` |
