"""Financial Datasets API tools for fetching financial statements and stock prices."""

from __future__ import annotations

import logging
import os

import httpx

from src.humcp.decorator import tool
from src.tools.finance.schemas import (
    FinancialDatasetsFinancialsData,
    FinancialDatasetsFinancialsResponse,
    FinancialDatasetsInsiderTradesData,
    FinancialDatasetsInsiderTradesResponse,
    FinancialDatasetsPricesData,
    FinancialDatasetsPricesResponse,
    FinancialStatement,
    InsiderTrade,
    PriceEntry,
)

logger = logging.getLogger("humcp.tools.financial_datasets")

BASE_URL = "https://api.financialdatasets.ai"


async def _make_request(endpoint: str, params: dict, api_key: str) -> dict:
    """Make an authenticated GET request to the Financial Datasets API.

    Args:
        endpoint: API endpoint path (e.g., 'financials/income-statements').
        params: Query parameters for the request.
        api_key: Financial Datasets API key.

    Returns:
        Parsed JSON response as a dictionary.
    """
    url = f"{BASE_URL}/{endpoint}"
    headers = {"X-API-KEY": api_key}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


@tool()
async def financial_datasets_get_financials(
    ticker: str,
    period: str = "annual",
) -> FinancialDatasetsFinancialsResponse:
    """
    Get income statements for a given stock ticker from the Financial Datasets API.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT').
        period: Reporting period: 'annual', 'quarterly', or 'ttm'. Defaults to 'annual'.

    Returns:
        Financial statement data or error message.
    """
    try:
        api_key = os.getenv("FINANCIAL_DATASETS_API_KEY")
        if not api_key:
            return FinancialDatasetsFinancialsResponse(
                success=False,
                error="FINANCIAL_DATASETS_API_KEY not configured. Contact administrator.",
            )

        valid_periods = {"annual", "quarterly", "ttm"}
        if period not in valid_periods:
            return FinancialDatasetsFinancialsResponse(
                success=False,
                error=f"Invalid period '{period}'. Valid periods: {', '.join(sorted(valid_periods))}",
            )

        logger.info("Fetching financials for %s period=%s", ticker, period)
        params = {"ticker": ticker, "period": period, "limit": 10}
        result = await _make_request("financials/income-statements", params, api_key)

        raw_statements = result.get("income_statements", [])
        statements = [
            FinancialStatement(
                ticker=ticker,
                period=period,
                data=stmt,
            )
            for stmt in raw_statements
        ]

        return FinancialDatasetsFinancialsResponse(
            success=True,
            data=FinancialDatasetsFinancialsData(
                ticker=ticker,
                period=period,
                statements=statements,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error fetching financials for %s", ticker)
        return FinancialDatasetsFinancialsResponse(
            success=False,
            error=f"API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to fetch financials for %s", ticker)
        return FinancialDatasetsFinancialsResponse(
            success=False,
            error=f"Error fetching financials for {ticker}: {e}",
        )


@tool()
async def financial_datasets_get_prices(
    ticker: str,
    period: str = "1d",
) -> FinancialDatasetsPricesResponse:
    """
    Get stock price data for a given ticker from the Financial Datasets API.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT').
        period: Price interval (e.g., '1d', '1h'). Defaults to '1d'.

    Returns:
        Stock price data or error message.
    """
    try:
        api_key = os.getenv("FINANCIAL_DATASETS_API_KEY")
        if not api_key:
            return FinancialDatasetsPricesResponse(
                success=False,
                error="FINANCIAL_DATASETS_API_KEY not configured. Contact administrator.",
            )

        logger.info("Fetching prices for %s period=%s", ticker, period)
        params = {"ticker": ticker, "interval": period, "limit": 100}
        result = await _make_request("prices", params, api_key)

        raw_prices = result.get("prices", [])
        prices = [
            PriceEntry(
                date=p.get("time") or p.get("date"),
                open=p.get("open"),
                high=p.get("high"),
                low=p.get("low"),
                close=p.get("close"),
                volume=p.get("volume"),
            )
            for p in raw_prices
        ]

        return FinancialDatasetsPricesResponse(
            success=True,
            data=FinancialDatasetsPricesData(
                ticker=ticker,
                prices=prices,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error fetching prices for %s", ticker)
        return FinancialDatasetsPricesResponse(
            success=False,
            error=f"API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to fetch prices for %s", ticker)
        return FinancialDatasetsPricesResponse(
            success=False,
            error=f"Error fetching prices for {ticker}: {e}",
        )


@tool()
async def financial_datasets_get_insider_trades(
    ticker: str,
    limit: int = 50,
) -> FinancialDatasetsInsiderTradesResponse:
    """
    Get insider trading data for a given stock ticker from the Financial Datasets API.

    Retrieves SEC-filed insider trades including purchases and sales by company
    officers, directors, and significant shareholders. Each trade includes the
    insider's name, title, transaction type, share count, price, and filing date.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'TSLA').
        limit: Maximum number of insider trade records to return (default 50).

    Returns:
        Insider trading data or error message.
    """
    try:
        api_key = os.getenv("FINANCIAL_DATASETS_API_KEY")
        if not api_key:
            return FinancialDatasetsInsiderTradesResponse(
                success=False,
                error="FINANCIAL_DATASETS_API_KEY not configured. Contact administrator.",
            )

        if limit < 1:
            return FinancialDatasetsInsiderTradesResponse(
                success=False,
                error="limit must be at least 1",
            )

        logger.info("Fetching insider trades for %s limit=%d", ticker, limit)
        params = {"ticker": ticker, "limit": min(limit, 500)}
        result = await _make_request("insider-trades", params, api_key)

        raw_trades = result.get("insider_trades", [])
        trades = [
            InsiderTrade(
                ticker=t.get("ticker"),
                company_name=t.get("company_name"),
                insider_name=t.get("full_name") or t.get("insider_name"),
                insider_title=t.get("title") or t.get("insider_title"),
                transaction_type=t.get("transaction_type"),
                shares=t.get("shares"),
                price_per_share=t.get("price_per_share"),
                total_value=t.get("total_value"),
                filing_date=t.get("filing_date"),
                transaction_date=t.get("transaction_date"),
            )
            for t in raw_trades
        ]

        return FinancialDatasetsInsiderTradesResponse(
            success=True,
            data=FinancialDatasetsInsiderTradesData(
                ticker=ticker,
                trades=trades,
                count=len(trades),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error fetching insider trades for %s", ticker)
        return FinancialDatasetsInsiderTradesResponse(
            success=False,
            error=f"API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to fetch insider trades for %s", ticker)
        return FinancialDatasetsInsiderTradesResponse(
            success=False,
            error=f"Error fetching insider trades for {ticker}: {e}",
        )
