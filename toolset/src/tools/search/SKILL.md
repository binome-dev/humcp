---
name: searching-web
description: Searches the web using multiple search engines (Tavily, DuckDuckGo, Brave, SerpAPI, Serper, SearXNG, Baidu, Exa, Seltz, Valyu). Use when the user needs current information, wants to search the internet, or asks questions requiring up-to-date web data. Choose the engine based on availability, region, or use case.
---

# Web Search Tools

Tools for searching the web using a variety of search engines and APIs.

## Available Search Engines

| Tool | API Key Required | Best For |
|------|-----------------|----------|
| `tavily_web_search` | `TAVILY_API_KEY` | General web search with AI-generated answers |
| `duckduckgo_search` | None (free) | Privacy-focused search, no API key needed |
| `duckduckgo_news` | None (free) | News search without API key |
| `brave_web_search` | `BRAVE_API_KEY` | Privacy-respecting web search |
| `serpapi_search` | `SERPAPI_API_KEY` | Google/Bing/Yahoo via SerpAPI with rich metadata |
| `serper_google_search` | `SERPER_API_KEY` | Fast Google search via Serper.dev |
| `searxng_search` | None (`SEARXNG_BASE_URL`) | Self-hosted meta-search engine |
| `baidu_search` | None (free) | Chinese language search via Baidu |
| `exa_search` | `EXA_API_KEY` | AI-native search with autoprompt and content retrieval |
| `seltz_search` | `SELTZ_API_KEY` | AI-powered document search |
| `valyu_search` | `VALYU_API_KEY` | Web and academic/proprietary source search |

## Environment Variables

Set the API keys for the engines you want to use:
- `TAVILY_API_KEY` - Tavily API key
- `BRAVE_API_KEY` - Brave Search API key
- `SERPAPI_API_KEY` - SerpAPI key
- `SERPER_API_KEY` - Serper.dev API key
- `SEARXNG_BASE_URL` - SearXNG instance URL (e.g., `http://localhost:8888`)
- `EXA_API_KEY` - Exa API key
- `SELTZ_API_KEY` - Seltz API key
- `VALYU_API_KEY` - Valyu API key
- `DUCKDUCKGO_PROXY` - Optional proxy for DuckDuckGo requests

## Quick Examples

### DuckDuckGo (no API key needed)

```python
result = await duckduckgo_search(
    query="latest Python release",
    max_results=5
)

news = await duckduckgo_news(
    query="AI breakthroughs",
    max_results=5,
    timelimit="w"  # past week
)
```

### Tavily

```python
result = await tavily_web_search(
    query="machine learning tutorials",
    max_results=5,
    search_depth="advanced"
)
```

### Brave Search

```python
result = await brave_web_search(
    query="climate change research",
    count=10,
    country="US"
)
```

### SerpAPI

```python
result = await serpapi_search(
    query="best programming languages 2025",
    engine="google",
    num_results=10
)
```

### Serper (Google)

```python
result = await serper_google_search(
    query="OpenAI GPT updates",
    num_results=10
)
```

### SearXNG (self-hosted)

```python
result = await searxng_search(
    query="quantum computing",
    categories="science",
    num_results=10
)
```

### Baidu (Chinese search)

```python
result = await baidu_search(
    query="artificial intelligence",
    max_results=5
)
```

### Exa (AI-native)

```python
result = await exa_search(
    query="transformer architecture papers",
    num_results=5,
    use_autoprompt=True,
    category="research paper"
)
```

### Seltz

```python
result = await seltz_search(
    query="Python async patterns",
    max_results=10,
    context="user is looking for advanced Python documentation"
)
```

### Valyu (web + academic)

```python
result = await valyu_search(
    query="CRISPR gene editing",
    search_type="proprietary",  # academic sources
    max_results=10
)
```

## Response Format

All search tools return a consistent response structure:

```json
{
  "success": true,
  "data": {
    "query": "search query",
    "results": [
      {
        "title": "Result Title",
        "url": "https://example.com",
        "snippet": "Content snippet...",
        "score": 0.95
      }
    ]
  }
}
```

Some engines include additional fields (e.g., `knowledge_graph` for SerpAPI, `autoprompt_string` for Exa, `search_type` for Valyu).

## When to Use

- **No API key available**: Use `duckduckgo_search` or `duckduckgo_news`
- **General web search**: Use `tavily_web_search`, `brave_web_search`, or `serper_google_search`
- **Academic/research**: Use `exa_search` (with category "research paper") or `valyu_search` (with search_type "proprietary")
- **Chinese content**: Use `baidu_search`
- **Self-hosted/private**: Use `searxng_search`
- **Rich metadata (knowledge graph, related questions)**: Use `serpapi_search`
- **AI-powered document search**: Use `seltz_search`
