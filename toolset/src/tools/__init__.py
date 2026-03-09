"""Tool modules for HuMCP server.

This package contains tool implementations organized by category:
- api/: Generic HTTP client
- audio/: Text-to-speech, transcription, Spotify
- calendar/: Cal.com, Zoom scheduling
- cloud/: AWS Lambda/SES, Docker, Daytona, E2B, Airflow
- data/: Data processing tools (CSV, pandas)
- database/: PostgreSQL, DuckDB, Neo4j, SQL, Redshift
- ecommerce/: Shopify, Brandfetch
- files/: File format tools
- finance/: Stock data (yfinance, OpenBB), crypto (EVM)
- google/: Google Workspace, Maps, BigQuery
- image/: Image processing tools
- local/: Calculator, filesystem, shell
- media/: Image/video generation (DALL-E, Replicate, Giphy, etc.)
- memory/: Persistent memory (Mem0, Zep)
- messaging/: Slack, Discord, Telegram, email, SMS
- project_management/: Jira, Linear, GitHub, Notion, etc.
- research/: arXiv, PubMed, Wikipedia
- search/: Web search (Tavily, DuckDuckGo, Brave, etc.)
- social/: Reddit, X/Twitter, HackerNews, YouTube
- storage/: MinIO S3-compatible object storage
- weather/: OpenWeatherMap
- web_scraping/: Crawl4AI, Firecrawl, Jina, etc.

Tools are auto-discovered at server startup from Python files in this package.
Use the @tool decorator from src.humcp.decorator to register new tools.

Example:
    from src.humcp.decorator import tool

    @tool(category="custom")  # or @tool() to auto-detect from folder
    async def my_tool(param: str) -> dict:
        '''Tool description (used by FastMCP).'''
        return {"success": True, "data": param}
"""

from src.humcp.decorator import tool

__all__ = ["tool"]
