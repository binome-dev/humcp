"""YFinance tools for fetching stock prices, company info, and historical data."""

from __future__ import annotations

import logging

from src.humcp.decorator import tool
from src.tools.finance.schemas import (
    DividendData,
    DividendEntry,
    DividendResponse,
    HistoricalPriceData,
    HistoricalPriceEntry,
    HistoricalPriceResponse,
    OptionContract,
    OptionsChainData,
    OptionsChainResponse,
    StockInfoData,
    StockInfoResponse,
    StockPriceData,
    StockPriceResponse,
)

try:
    import yfinance as yf
except ImportError as err:
    raise ImportError(
        "yfinance is required for YFinance tools. Install with: pip install yfinance"
    ) from err

logger = logging.getLogger("humcp.tools.yfinance")


@tool()
async def yfinance_get_stock_price(symbol: str) -> StockPriceResponse:
    """
    Get the current stock price for a given ticker symbol using Yahoo Finance.

    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT').

    Returns:
        Current stock price data or error message.
    """
    try:
        logger.info("Fetching current price for %s", symbol)
        stock = yf.Ticker(symbol)
        info = stock.info
        current_price = info.get("regularMarketPrice", info.get("currentPrice"))
        currency = info.get("currency", "USD")

        if current_price is None:
            return StockPriceResponse(
                success=False,
                error=f"Could not fetch current price for {symbol}",
            )

        return StockPriceResponse(
            success=True,
            data=StockPriceData(
                symbol=symbol,
                price=current_price,
                currency=currency,
            ),
        )
    except Exception as e:
        logger.exception("Failed to fetch stock price for %s", symbol)
        return StockPriceResponse(
            success=False,
            error=f"Error fetching stock price for {symbol}: {e}",
        )


@tool()
async def yfinance_get_stock_info(symbol: str) -> StockInfoResponse:
    """
    Get detailed company information for a given stock symbol using Yahoo Finance.

    Returns company name, sector, industry, market cap, P/E ratio, EPS,
    52-week range, dividend yield, and business summary.

    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT').

    Returns:
        Company information data or error message.
    """
    try:
        logger.info("Fetching stock info for %s", symbol)
        stock = yf.Ticker(symbol)
        info = stock.info

        if not info:
            return StockInfoResponse(
                success=False,
                error=f"Could not fetch company info for {symbol}",
            )

        return StockInfoResponse(
            success=True,
            data=StockInfoData(
                symbol=symbol,
                name=info.get("shortName"),
                sector=info.get("sector"),
                industry=info.get("industry"),
                market_cap=info.get("marketCap"),
                pe_ratio=info.get("trailingPE"),
                eps=info.get("trailingEps"),
                fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
                fifty_two_week_low=info.get("fiftyTwoWeekLow"),
                dividend_yield=info.get("dividendYield"),
                summary=info.get("longBusinessSummary"),
            ),
        )
    except Exception as e:
        logger.exception("Failed to fetch stock info for %s", symbol)
        return StockInfoResponse(
            success=False,
            error=f"Error fetching stock info for {symbol}: {e}",
        )


@tool()
async def yfinance_get_historical_data(
    symbol: str,
    period: str = "1mo",
) -> HistoricalPriceResponse:
    """
    Get historical stock price data for a given symbol using Yahoo Finance.

    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT').
        period: Time period for historical data. Valid values: 1d, 5d, 1mo, 3mo,
                6mo, 1y, 2y, 5y, 10y, ytd, max. Defaults to '1mo'.

    Returns:
        Historical price data or error message.
    """
    try:
        valid_periods = {
            "1d",
            "5d",
            "1mo",
            "3mo",
            "6mo",
            "1y",
            "2y",
            "5y",
            "10y",
            "ytd",
            "max",
        }
        if period not in valid_periods:
            return HistoricalPriceResponse(
                success=False,
                error=f"Invalid period '{period}'. Valid periods: {', '.join(sorted(valid_periods))}",
            )

        logger.info("Fetching historical data for %s period=%s", symbol, period)
        stock = yf.Ticker(symbol)
        history = stock.history(period=period)

        if history.empty:
            return HistoricalPriceResponse(
                success=False,
                error=f"No historical data found for {symbol} with period {period}",
            )

        prices = [
            HistoricalPriceEntry(
                date=str(date.date()),
                open=round(row.get("Open", 0), 4)
                if row.get("Open") is not None
                else None,
                high=round(row.get("High", 0), 4)
                if row.get("High") is not None
                else None,
                low=round(row.get("Low", 0), 4) if row.get("Low") is not None else None,
                close=round(row.get("Close", 0), 4)
                if row.get("Close") is not None
                else None,
                volume=int(row.get("Volume", 0))
                if row.get("Volume") is not None
                else None,
            )
            for date, row in history.iterrows()
        ]

        return HistoricalPriceResponse(
            success=True,
            data=HistoricalPriceData(
                symbol=symbol,
                period=period,
                prices=prices,
            ),
        )
    except Exception as e:
        logger.exception("Failed to fetch historical data for %s", symbol)
        return HistoricalPriceResponse(
            success=False,
            error=f"Error fetching historical data for {symbol}: {e}",
        )


@tool()
async def yfinance_get_dividends(symbol: str) -> DividendResponse:
    """
    Get the dividend payment history for a given stock ticker symbol using Yahoo Finance.

    Returns a chronological list of ex-dividend dates and per-share dividend amounts.
    Useful for analyzing income-generating stocks, tracking payout trends, and
    calculating dividend yields over time.

    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL', 'MSFT', 'JNJ').

    Returns:
        Dividend history with dates and amounts, or error message.
    """
    try:
        logger.info("Fetching dividends for %s", symbol)
        stock = yf.Ticker(symbol)
        dividends = stock.dividends

        if dividends is None or dividends.empty:
            return DividendResponse(
                success=False,
                error=f"No dividend data found for {symbol}. The stock may not pay dividends.",
            )

        entries = [
            DividendEntry(
                date=str(date.date()),
                dividend=round(float(amount), 6),
            )
            for date, amount in dividends.items()
        ]

        return DividendResponse(
            success=True,
            data=DividendData(
                symbol=symbol,
                dividends=entries,
                count=len(entries),
            ),
        )
    except Exception as e:
        logger.exception("Failed to fetch dividends for %s", symbol)
        return DividendResponse(
            success=False,
            error=f"Error fetching dividends for {symbol}: {e}",
        )


@tool()
async def yfinance_get_options(
    symbol: str,
    expiration: str | None = None,
) -> OptionsChainResponse:
    """
    Get the options chain for a given stock ticker symbol using Yahoo Finance.

    Retrieves call and put option contracts for a specific expiration date.
    If no expiration date is provided, the nearest available expiration is used.
    Each contract includes strike price, bid/ask, volume, open interest, and
    implied volatility.

    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL', 'TSLA', 'SPY').
        expiration: Options expiration date in 'YYYY-MM-DD' format. If None,
                    uses the nearest available expiration date.

    Returns:
        Options chain with calls and puts for the given expiration, or error message.
    """
    try:
        logger.info("Fetching options for %s expiration=%s", symbol, expiration)
        stock = yf.Ticker(symbol)

        available_expirations = list(stock.options) if stock.options else []
        if not available_expirations:
            return OptionsChainResponse(
                success=False,
                error=f"No options data available for {symbol}.",
            )

        selected_expiration = expiration if expiration else available_expirations[0]

        if selected_expiration not in available_expirations:
            return OptionsChainResponse(
                success=False,
                error=f"Expiration '{selected_expiration}' not available for {symbol}. "
                f"Available: {', '.join(available_expirations[:10])}",
            )

        chain = stock.option_chain(selected_expiration)

        def _parse_contracts(df) -> list[OptionContract]:
            contracts: list[OptionContract] = []
            for _, row in df.iterrows():
                contracts.append(
                    OptionContract(
                        contract_symbol=row.get("contractSymbol"),
                        strike=row.get("strike"),
                        last_price=row.get("lastPrice"),
                        bid=row.get("bid"),
                        ask=row.get("ask"),
                        volume=int(row["volume"])
                        if row.get("volume") is not None and not _is_nan(row["volume"])
                        else None,
                        open_interest=int(row["openInterest"])
                        if row.get("openInterest") is not None
                        and not _is_nan(row["openInterest"])
                        else None,
                        implied_volatility=round(float(row["impliedVolatility"]), 6)
                        if row.get("impliedVolatility") is not None
                        and not _is_nan(row["impliedVolatility"])
                        else None,
                        in_the_money=bool(row.get("inTheMoney"))
                        if row.get("inTheMoney") is not None
                        else None,
                    )
                )
            return contracts

        calls = (
            _parse_contracts(chain.calls)
            if chain.calls is not None and not chain.calls.empty
            else []
        )
        puts = (
            _parse_contracts(chain.puts)
            if chain.puts is not None and not chain.puts.empty
            else []
        )

        return OptionsChainResponse(
            success=True,
            data=OptionsChainData(
                symbol=symbol,
                expiration=selected_expiration,
                available_expirations=available_expirations,
                calls=calls,
                puts=puts,
            ),
        )
    except Exception as e:
        logger.exception("Failed to fetch options for %s", symbol)
        return OptionsChainResponse(
            success=False,
            error=f"Error fetching options for {symbol}: {e}",
        )


def _is_nan(value) -> bool:
    """Check if a value is NaN."""
    try:
        import math

        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False
