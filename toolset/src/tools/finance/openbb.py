"""OpenBB tools for fetching stock data and searching equities."""

from __future__ import annotations

import logging
import os

from src.humcp.decorator import tool
from src.tools.finance.schemas import (
    OpenBBMarketNewsData,
    OpenBBMarketNewsResponse,
    OpenBBNewsArticle,
    OpenBBSearchData,
    OpenBBSearchResponse,
    OpenBBSearchResult,
    OpenBBStockData,
    OpenBBStockDataResponse,
    OpenBBStockQuote,
)

try:
    from openbb import obb as openbb_app
except ImportError as err:
    raise ImportError(
        "openbb is required for OpenBB tools. Install with: pip install openbb"
    ) from err

logger = logging.getLogger("humcp.tools.openbb")


def _get_openbb_client():
    """Return the OpenBB client, authenticating if a PAT is available."""
    token = os.getenv("OPENBB_TOKEN")
    if token:
        try:
            openbb_app.account.login(pat=token)
        except Exception as e:
            logger.warning("OpenBB PAT login failed: %s", e)
    return openbb_app


@tool()
async def openbb_get_stock_data(symbol: str) -> OpenBBStockDataResponse:
    """
    Get current stock quote data for one or more symbols using OpenBB.

    Supports multiple symbols separated by commas (e.g., 'AAPL,MSFT,GOOGL').

    Args:
        symbol: Stock ticker symbol or comma-separated list of symbols
                (e.g., 'AAPL' or 'AAPL,MSFT,GOOGL').

    Returns:
        Stock quote data or error message.
    """
    try:
        logger.info("Fetching stock data for %s via OpenBB", symbol)
        obb = _get_openbb_client()
        result = obb.equity.price.quote(symbol=symbol, provider="yfinance").to_polars()

        quotes = [
            OpenBBStockQuote(
                symbol=row.get("symbol"),
                last_price=row.get("last_price"),
                currency=row.get("currency"),
                name=row.get("name"),
                high=row.get("high"),
                low=row.get("low"),
                open=row.get("open"),
                close=row.get("close"),
                volume=row.get("volume"),
            )
            for row in result.to_dicts()
        ]

        return OpenBBStockDataResponse(
            success=True,
            data=OpenBBStockData(quotes=quotes),
        )
    except Exception as e:
        logger.exception("Failed to fetch stock data for %s", symbol)
        return OpenBBStockDataResponse(
            success=False,
            error=f"Error fetching stock data for {symbol}: {e}",
        )


@tool()
async def openbb_search_stocks(query: str) -> OpenBBSearchResponse:
    """
    Search for stock ticker symbols by company name using OpenBB.

    Args:
        query: Company name or partial name to search for (e.g., 'Apple', 'Tesla').

    Returns:
        List of matching stock symbols and company names, or error message.
    """
    try:
        logger.info("Searching stocks for query=%s via OpenBB", query)
        obb = _get_openbb_client()
        result = obb.equity.search(query).to_polars()

        results = [
            OpenBBSearchResult(
                symbol=row.get("symbol"),
                name=row.get("name"),
            )
            for row in result.to_dicts()
        ]

        return OpenBBSearchResponse(
            success=True,
            data=OpenBBSearchData(query=query, results=results),
        )
    except Exception as e:
        logger.exception("Failed to search stocks for %s", query)
        return OpenBBSearchResponse(
            success=False,
            error=f"Error searching stocks for '{query}': {e}",
        )


@tool()
async def openbb_get_market_news(
    limit: int = 20,
) -> OpenBBMarketNewsResponse:
    """
    Get the latest market news headlines using OpenBB.

    Fetches recent financial and market news articles from available providers.
    Each article includes the headline, publication date, summary text, source
    URL, related ticker symbols, and publisher name.

    Args:
        limit: Maximum number of news articles to return (1-100). Defaults to 20.

    Returns:
        List of market news articles, or error message.
    """
    try:
        clamped_limit = max(1, min(limit, 100))

        logger.info("Fetching market news limit=%d via OpenBB", clamped_limit)
        obb = _get_openbb_client()
        result = obb.news.world(limit=clamped_limit, provider="benzinga").to_polars()

        articles = [
            OpenBBNewsArticle(
                title=row.get("title"),
                date=str(row.get("date")) if row.get("date") else None,
                text=row.get("text"),
                url=row.get("url"),
                symbols=row.get("symbols"),
                source=row.get("source"),
            )
            for row in result.to_dicts()
        ]

        return OpenBBMarketNewsResponse(
            success=True,
            data=OpenBBMarketNewsData(
                articles=articles,
                count=len(articles),
            ),
        )
    except Exception as e:
        logger.exception("Failed to fetch market news")
        return OpenBBMarketNewsResponse(
            success=False,
            error=f"Error fetching market news: {e}",
        )
