"""Pydantic output schemas for finance tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# YFinance Schemas
# =============================================================================


class StockPriceData(BaseModel):
    """Output data for yfinance_get_stock_price tool."""

    symbol: str = Field(..., description="The stock ticker symbol")
    price: float | None = Field(None, description="Current regular market price")
    currency: str = Field("USD", description="Currency of the price")


class StockInfoData(BaseModel):
    """Output data for yfinance_get_stock_info tool."""

    symbol: str = Field(..., description="The stock ticker symbol")
    name: str | None = Field(None, description="Company short name")
    sector: str | None = Field(None, description="Company sector")
    industry: str | None = Field(None, description="Company industry")
    market_cap: int | None = Field(None, description="Market capitalization")
    pe_ratio: float | None = Field(None, description="Trailing P/E ratio")
    eps: float | None = Field(None, description="Trailing EPS")
    fifty_two_week_high: float | None = Field(None, description="52-week high price")
    fifty_two_week_low: float | None = Field(None, description="52-week low price")
    dividend_yield: float | None = Field(None, description="Dividend yield")
    summary: str | None = Field(None, description="Company business summary")


class HistoricalPriceEntry(BaseModel):
    """A single historical price data point."""

    date: str = Field(..., description="Date of the price data")
    open: float | None = Field(None, description="Opening price")
    high: float | None = Field(None, description="High price")
    low: float | None = Field(None, description="Low price")
    close: float | None = Field(None, description="Closing price")
    volume: int | None = Field(None, description="Trading volume")


class HistoricalPriceData(BaseModel):
    """Output data for yfinance_get_historical_data tool."""

    symbol: str = Field(..., description="The stock ticker symbol")
    period: str = Field(..., description="Time period of the data")
    prices: list[HistoricalPriceEntry] = Field(
        default_factory=list, description="List of historical price entries"
    )


class DividendEntry(BaseModel):
    """A single dividend payment data point."""

    date: str = Field(..., description="Ex-dividend date")
    dividend: float = Field(..., description="Dividend amount per share")


class DividendData(BaseModel):
    """Output data for yfinance_get_dividends tool."""

    symbol: str = Field(..., description="The stock ticker symbol")
    dividends: list[DividendEntry] = Field(
        default_factory=list, description="List of dividend payments"
    )
    count: int = Field(0, description="Number of dividend entries returned")


class OptionContract(BaseModel):
    """A single option contract."""

    contract_symbol: str | None = Field(None, description="Option contract symbol")
    strike: float | None = Field(None, description="Strike price")
    last_price: float | None = Field(None, description="Last traded price")
    bid: float | None = Field(None, description="Bid price")
    ask: float | None = Field(None, description="Ask price")
    volume: int | None = Field(None, description="Trading volume")
    open_interest: int | None = Field(None, description="Open interest")
    implied_volatility: float | None = Field(None, description="Implied volatility")
    in_the_money: bool | None = Field(
        None, description="Whether the option is in the money"
    )


class OptionsChainData(BaseModel):
    """Output data for yfinance_get_options tool."""

    symbol: str = Field(..., description="The stock ticker symbol")
    expiration: str = Field(..., description="Options expiration date")
    available_expirations: list[str] = Field(
        default_factory=list, description="All available expiration dates"
    )
    calls: list[OptionContract] = Field(
        default_factory=list, description="List of call option contracts"
    )
    puts: list[OptionContract] = Field(
        default_factory=list, description="List of put option contracts"
    )


# =============================================================================
# OpenBB Schemas
# =============================================================================


class OpenBBStockQuote(BaseModel):
    """A single stock quote from OpenBB."""

    symbol: str | None = Field(None, description="Stock ticker symbol")
    last_price: float | None = Field(None, description="Last traded price")
    currency: str | None = Field(None, description="Price currency")
    name: str | None = Field(None, description="Company name")
    high: float | None = Field(None, description="Day high price")
    low: float | None = Field(None, description="Day low price")
    open: float | None = Field(None, description="Day opening price")
    close: float | None = Field(None, description="Previous close price")
    volume: int | None = Field(None, description="Trading volume")


class OpenBBStockData(BaseModel):
    """Output data for openbb_get_stock_data tool."""

    quotes: list[OpenBBStockQuote] = Field(
        default_factory=list, description="List of stock quotes"
    )


class OpenBBSearchResult(BaseModel):
    """A single search result from OpenBB."""

    symbol: str | None = Field(None, description="Stock ticker symbol")
    name: str | None = Field(None, description="Company name")


class OpenBBSearchData(BaseModel):
    """Output data for openbb_search_stocks tool."""

    query: str = Field(..., description="The search query")
    results: list[OpenBBSearchResult] = Field(
        default_factory=list, description="List of matching stocks"
    )


# =============================================================================
# OpenBB Market News Schemas
# =============================================================================


class OpenBBNewsArticle(BaseModel):
    """A single news article from OpenBB."""

    title: str | None = Field(None, description="Article headline")
    date: str | None = Field(None, description="Publication date")
    text: str | None = Field(None, description="Article text or summary")
    url: str | None = Field(None, description="URL to the full article")
    symbols: str | None = Field(None, description="Related ticker symbols")
    source: str | None = Field(None, description="News source or publisher")


class OpenBBMarketNewsData(BaseModel):
    """Output data for openbb_get_market_news tool."""

    articles: list[OpenBBNewsArticle] = Field(
        default_factory=list, description="List of market news articles"
    )
    count: int = Field(0, description="Number of articles returned")


# =============================================================================
# Financial Datasets Schemas
# =============================================================================


class FinancialStatement(BaseModel):
    """A single financial statement entry."""

    ticker: str = Field(..., description="Stock ticker symbol")
    period: str = Field(..., description="Reporting period (annual/quarterly/ttm)")
    data: dict = Field(default_factory=dict, description="Financial statement data")


class FinancialDatasetsFinancialsData(BaseModel):
    """Output data for financial_datasets_get_financials tool."""

    ticker: str = Field(..., description="Stock ticker symbol")
    period: str = Field(..., description="Reporting period")
    statements: list[FinancialStatement] = Field(
        default_factory=list, description="List of financial statements"
    )


class PriceEntry(BaseModel):
    """A single price data point from Financial Datasets."""

    date: str | None = Field(None, description="Date of the price data")
    open: float | None = Field(None, description="Opening price")
    high: float | None = Field(None, description="High price")
    low: float | None = Field(None, description="Low price")
    close: float | None = Field(None, description="Closing price")
    volume: int | None = Field(None, description="Trading volume")


class FinancialDatasetsPricesData(BaseModel):
    """Output data for financial_datasets_get_prices tool."""

    ticker: str = Field(..., description="Stock ticker symbol")
    prices: list[PriceEntry] = Field(
        default_factory=list, description="List of price data points"
    )


class InsiderTrade(BaseModel):
    """A single insider trade record."""

    ticker: str | None = Field(None, description="Stock ticker symbol")
    company_name: str | None = Field(None, description="Company name")
    insider_name: str | None = Field(None, description="Name of the insider")
    insider_title: str | None = Field(
        None, description="Title or position of the insider"
    )
    transaction_type: str | None = Field(
        None, description="Transaction type (e.g., 'Buy', 'Sell')"
    )
    shares: int | None = Field(None, description="Number of shares traded")
    price_per_share: float | None = Field(
        None, description="Price per share at time of trade"
    )
    total_value: float | None = Field(
        None, description="Total value of the transaction"
    )
    filing_date: str | None = Field(None, description="SEC filing date")
    transaction_date: str | None = Field(None, description="Date of the transaction")


class FinancialDatasetsInsiderTradesData(BaseModel):
    """Output data for financial_datasets_get_insider_trades tool."""

    ticker: str = Field(..., description="Stock ticker symbol")
    trades: list[InsiderTrade] = Field(
        default_factory=list, description="List of insider trades"
    )
    count: int = Field(0, description="Number of insider trades returned")


# =============================================================================
# EVM Schemas
# =============================================================================


class EvmBalanceData(BaseModel):
    """Output data for evm_get_balance tool."""

    address: str = Field(..., description="Wallet address")
    balance_wei: str = Field(..., description="Balance in wei")
    balance_eth: str = Field(..., description="Balance in ETH (or native token)")
    chain: str = Field(..., description="Blockchain chain identifier")


class EvmTransactionData(BaseModel):
    """Output data for evm_get_transaction tool."""

    tx_hash: str = Field(..., description="Transaction hash")
    from_address: str | None = Field(None, description="Sender address")
    to_address: str | None = Field(None, description="Recipient address")
    value_wei: str | None = Field(None, description="Transaction value in wei")
    gas_used: int | None = Field(None, description="Gas used by the transaction")
    block_number: int | None = Field(None, description="Block number")
    status: int | None = Field(
        None, description="Transaction status (1=success, 0=fail)"
    )
    chain: str = Field(..., description="Blockchain chain identifier")


class EvmBlockData(BaseModel):
    """Output data for evm_get_block tool."""

    block_number: int = Field(..., description="Block number")
    block_hash: str | None = Field(None, description="Block hash")
    parent_hash: str | None = Field(None, description="Parent block hash")
    timestamp: int | None = Field(None, description="Block timestamp (Unix epoch)")
    gas_used: int | None = Field(None, description="Total gas used in the block")
    gas_limit: int | None = Field(None, description="Block gas limit")
    transaction_count: int = Field(0, description="Number of transactions in the block")
    miner: str | None = Field(None, description="Miner/validator address")
    chain: str = Field(..., description="Blockchain chain identifier")


class EvmGasPriceData(BaseModel):
    """Output data for evm_get_gas_price tool."""

    gas_price_wei: str = Field(..., description="Current gas price in wei")
    gas_price_gwei: str = Field(..., description="Current gas price in Gwei")
    chain: str = Field(..., description="Blockchain chain identifier")


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class StockPriceResponse(ToolResponse[StockPriceData]):
    """Response schema for yfinance_get_stock_price tool."""

    pass


class StockInfoResponse(ToolResponse[StockInfoData]):
    """Response schema for yfinance_get_stock_info tool."""

    pass


class HistoricalPriceResponse(ToolResponse[HistoricalPriceData]):
    """Response schema for yfinance_get_historical_data tool."""

    pass


class OpenBBStockDataResponse(ToolResponse[OpenBBStockData]):
    """Response schema for openbb_get_stock_data tool."""

    pass


class OpenBBSearchResponse(ToolResponse[OpenBBSearchData]):
    """Response schema for openbb_search_stocks tool."""

    pass


class OpenBBMarketNewsResponse(ToolResponse[OpenBBMarketNewsData]):
    """Response schema for openbb_get_market_news tool."""

    pass


class FinancialDatasetsFinancialsResponse(
    ToolResponse[FinancialDatasetsFinancialsData]
):
    """Response schema for financial_datasets_get_financials tool."""

    pass


class FinancialDatasetsPricesResponse(ToolResponse[FinancialDatasetsPricesData]):
    """Response schema for financial_datasets_get_prices tool."""

    pass


class EvmBalanceResponse(ToolResponse[EvmBalanceData]):
    """Response schema for evm_get_balance tool."""

    pass


class EvmTransactionResponse(ToolResponse[EvmTransactionData]):
    """Response schema for evm_get_transaction tool."""

    pass


class EvmBlockResponse(ToolResponse[EvmBlockData]):
    """Response schema for evm_get_block tool."""

    pass


class EvmGasPriceResponse(ToolResponse[EvmGasPriceData]):
    """Response schema for evm_get_gas_price tool."""

    pass


class DividendResponse(ToolResponse[DividendData]):
    """Response schema for yfinance_get_dividends tool."""

    pass


class OptionsChainResponse(ToolResponse[OptionsChainData]):
    """Response schema for yfinance_get_options tool."""

    pass


class FinancialDatasetsInsiderTradesResponse(
    ToolResponse[FinancialDatasetsInsiderTradesData]
):
    """Response schema for financial_datasets_get_insider_trades tool."""

    pass
