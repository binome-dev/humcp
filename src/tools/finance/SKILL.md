---
name: finance
description: Financial data tools for stock prices, company information, financial statements, and blockchain queries. Use when the user needs stock market data, company fundamentals, historical prices, or EVM blockchain information.
---

# Finance Tools

Tools for accessing financial market data, company information, and blockchain networks.

## Available Tools

### YFinance (No API key required)

- `yfinance_get_stock_price` - Get current stock price
- `yfinance_get_stock_info` - Get detailed company information
- `yfinance_get_historical_data` - Get historical price data

### OpenBB (Optional: OPENBB_TOKEN)

- `openbb_get_stock_data` - Get stock quotes (supports multiple symbols)
- `openbb_search_stocks` - Search for stocks by company name

### Financial Datasets (Required: FINANCIAL_DATASETS_API_KEY)

- `financial_datasets_get_financials` - Get income statements
- `financial_datasets_get_prices` - Get stock price data

### EVM Blockchain (Optional: EVM_RPC_URL)

- `evm_get_balance` - Get wallet balance on EVM chains
- `evm_get_transaction` - Get transaction details by hash

## Requirements

Set environment variables as needed:
- `OPENBB_TOKEN`: OpenBB Personal Access Token (optional)
- `FINANCIAL_DATASETS_API_KEY`: Financial Datasets API key
- `EVM_RPC_URL`: Custom EVM RPC endpoint (defaults provided for major chains)

## Examples

### Get a stock price

```python
result = await yfinance_get_stock_price(symbol="AAPL")
```

### Response format

```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "price": 178.72,
    "currency": "USD"
  }
}
```

### Get historical data

```python
result = await yfinance_get_historical_data(
    symbol="MSFT",
    period="3mo"
)
```

### Check blockchain balance

```python
result = await evm_get_balance(
    address="0x742d35Cc6634C0532925a3b844Bc9e7595f2bD1e",
    chain="ethereum"
)
```

## When to Use

- Looking up current or historical stock prices
- Researching company fundamentals and financials
- Searching for stock ticker symbols
- Checking EVM wallet balances or transaction details
- Getting income statements or financial metrics
