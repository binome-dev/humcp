"""EVM blockchain tools for querying balances and transactions via JSON-RPC."""

from __future__ import annotations

import logging

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.finance.schemas import (
    EvmBalanceData,
    EvmBalanceResponse,
    EvmBlockData,
    EvmBlockResponse,
    EvmGasPriceData,
    EvmGasPriceResponse,
    EvmTransactionData,
    EvmTransactionResponse,
)

logger = logging.getLogger("humcp.tools.evm")

# Default chain RPC URLs when no EVM_RPC_URL is set
DEFAULT_RPC_URLS: dict[str, str] = {
    "ethereum": "https://eth.llamarpc.com",
    "polygon": "https://polygon-rpc.com",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
    "optimism": "https://mainnet.optimism.io",
    "base": "https://mainnet.base.org",
}


def _get_rpc_url(chain: str, env_url: str | None = None) -> str | None:
    """Resolve the RPC URL from a provided value or defaults.

    Args:
        chain: Chain identifier (e.g., 'ethereum', 'polygon').
        env_url: Optional RPC URL from credential resolution.

    Returns:
        The RPC URL string or None if not configured.
    """
    if env_url:
        return env_url
    return DEFAULT_RPC_URLS.get(chain.lower())


async def _rpc_call(rpc_url: str, method: str, params: list) -> dict:
    """Make a JSON-RPC call to an EVM node.

    Args:
        rpc_url: The RPC endpoint URL.
        method: The JSON-RPC method name.
        params: The method parameters.

    Returns:
        The JSON-RPC result.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(rpc_url, json=payload)
        response.raise_for_status()
        data = response.json()

    if "error" in data:
        raise ValueError(f"RPC error: {data['error'].get('message', data['error'])}")

    return data


@tool()
async def evm_get_balance(
    address: str,
    chain: str = "ethereum",
) -> EvmBalanceResponse:
    """
    Get the native token balance of an EVM wallet address.

    Queries the balance using JSON-RPC eth_getBalance. Supports Ethereum,
    Polygon, Arbitrum, Optimism, and Base chains by default.

    Args:
        address: The wallet address (0x-prefixed hex string).
        chain: Blockchain to query. Defaults to 'ethereum'. Supported chains:
               ethereum, polygon, arbitrum, optimism, base. Can also use a
               custom chain if EVM_RPC_URL is set.

    Returns:
        Wallet balance in wei and ETH (or native token), or error message.
    """
    try:
        env_url = await resolve_credential("EVM_RPC_URL")
        rpc_url = _get_rpc_url(chain, env_url)
        if not rpc_url:
            return EvmBalanceResponse(
                success=False,
                error=f"No RPC URL configured for chain '{chain}'. "
                f"Set EVM_RPC_URL or use a supported chain: {', '.join(DEFAULT_RPC_URLS.keys())}",
            )

        if not address.startswith("0x") or len(address) != 42:
            return EvmBalanceResponse(
                success=False,
                error=f"Invalid address format: '{address}'. Must be a 0x-prefixed 40-char hex string.",
            )

        logger.info("Fetching balance for %s on %s", address, chain)
        result = await _rpc_call(rpc_url, "eth_getBalance", [address, "latest"])

        balance_hex = result.get("result", "0x0")
        balance_wei = int(balance_hex, 16)
        balance_eth = balance_wei / 1e18

        return EvmBalanceResponse(
            success=True,
            data=EvmBalanceData(
                address=address,
                balance_wei=str(balance_wei),
                balance_eth=f"{balance_eth:.18f}",
                chain=chain,
            ),
        )
    except Exception as e:
        logger.exception("Failed to fetch balance for %s on %s", address, chain)
        return EvmBalanceResponse(
            success=False,
            error=f"Error fetching balance for {address} on {chain}: {e}",
        )


@tool()
async def evm_get_transaction(
    tx_hash: str,
    chain: str = "ethereum",
) -> EvmTransactionResponse:
    """
    Get details of a transaction by its hash from an EVM-compatible blockchain.

    Retrieves the transaction data and receipt (including status and gas used)
    using JSON-RPC eth_getTransactionByHash and eth_getTransactionReceipt.

    Args:
        tx_hash: The transaction hash (0x-prefixed hex string).
        chain: Blockchain to query. Defaults to 'ethereum'. Supported chains:
               ethereum, polygon, arbitrum, optimism, base.

    Returns:
        Transaction details or error message.
    """
    try:
        env_url = await resolve_credential("EVM_RPC_URL")
        rpc_url = _get_rpc_url(chain, env_url)
        if not rpc_url:
            return EvmTransactionResponse(
                success=False,
                error=f"No RPC URL configured for chain '{chain}'. "
                f"Set EVM_RPC_URL or use a supported chain: {', '.join(DEFAULT_RPC_URLS.keys())}",
            )

        if not tx_hash.startswith("0x"):
            return EvmTransactionResponse(
                success=False,
                error=f"Invalid transaction hash format: '{tx_hash}'. Must be 0x-prefixed.",
            )

        logger.info("Fetching transaction %s on %s", tx_hash, chain)

        tx_result = await _rpc_call(rpc_url, "eth_getTransactionByHash", [tx_hash])
        tx_data = tx_result.get("result")

        if not tx_data:
            return EvmTransactionResponse(
                success=False,
                error=f"Transaction not found: {tx_hash}",
            )

        # Fetch the receipt for status and gas used
        receipt_result = await _rpc_call(
            rpc_url, "eth_getTransactionReceipt", [tx_hash]
        )
        receipt = receipt_result.get("result", {})

        value_hex = tx_data.get("value", "0x0")
        value_wei = str(int(value_hex, 16))
        gas_used = (
            int(receipt.get("gasUsed", "0x0"), 16) if receipt.get("gasUsed") else None
        )
        block_number = (
            int(tx_data.get("blockNumber", "0x0"), 16)
            if tx_data.get("blockNumber")
            else None
        )
        status = (
            int(receipt.get("status", "0x0"), 16) if receipt.get("status") else None
        )

        return EvmTransactionResponse(
            success=True,
            data=EvmTransactionData(
                tx_hash=tx_hash,
                from_address=tx_data.get("from"),
                to_address=tx_data.get("to"),
                value_wei=value_wei,
                gas_used=gas_used,
                block_number=block_number,
                status=status,
                chain=chain,
            ),
        )
    except Exception as e:
        logger.exception("Failed to fetch transaction %s on %s", tx_hash, chain)
        return EvmTransactionResponse(
            success=False,
            error=f"Error fetching transaction {tx_hash} on {chain}: {e}",
        )


@tool()
async def evm_get_block(
    block_number: str = "latest",
    chain: str = "ethereum",
) -> EvmBlockResponse:
    """
    Get block information from an EVM-compatible blockchain by block number.

    Retrieves block metadata including hash, timestamp, gas usage, transaction
    count, and miner/validator address using JSON-RPC eth_getBlockByNumber.
    Supports Ethereum, Polygon, Arbitrum, Optimism, and Base chains by default.

    Args:
        block_number: Block number as a decimal string (e.g., '12345678') or
                      'latest' for the most recent block. Defaults to 'latest'.
        chain: Blockchain to query. Defaults to 'ethereum'. Supported chains:
               ethereum, polygon, arbitrum, optimism, base. Can also use a
               custom chain if EVM_RPC_URL is set.

    Returns:
        Block information including hash, timestamp, gas, and transaction count,
        or error message.
    """
    try:
        env_url = await resolve_credential("EVM_RPC_URL")
        rpc_url = _get_rpc_url(chain, env_url)
        if not rpc_url:
            return EvmBlockResponse(
                success=False,
                error=f"No RPC URL configured for chain '{chain}'. "
                f"Set EVM_RPC_URL or use a supported chain: {', '.join(DEFAULT_RPC_URLS.keys())}",
            )

        if block_number == "latest":
            block_param = "latest"
        else:
            try:
                block_param = hex(int(block_number))
            except ValueError:
                return EvmBlockResponse(
                    success=False,
                    error=f"Invalid block number: '{block_number}'. Must be a decimal number or 'latest'.",
                )

        logger.info("Fetching block %s on %s", block_number, chain)
        result = await _rpc_call(rpc_url, "eth_getBlockByNumber", [block_param, False])

        block = result.get("result")
        if not block:
            return EvmBlockResponse(
                success=False,
                error=f"Block not found: {block_number}",
            )

        parsed_block_number = int(block.get("number", "0x0"), 16)
        timestamp = (
            int(block.get("timestamp", "0x0"), 16) if block.get("timestamp") else None
        )
        gas_used = (
            int(block.get("gasUsed", "0x0"), 16) if block.get("gasUsed") else None
        )
        gas_limit = (
            int(block.get("gasLimit", "0x0"), 16) if block.get("gasLimit") else None
        )
        transactions = block.get("transactions", [])

        return EvmBlockResponse(
            success=True,
            data=EvmBlockData(
                block_number=parsed_block_number,
                block_hash=block.get("hash"),
                parent_hash=block.get("parentHash"),
                timestamp=timestamp,
                gas_used=gas_used,
                gas_limit=gas_limit,
                transaction_count=len(transactions),
                miner=block.get("miner"),
                chain=chain,
            ),
        )
    except Exception as e:
        logger.exception("Failed to fetch block %s on %s", block_number, chain)
        return EvmBlockResponse(
            success=False,
            error=f"Error fetching block {block_number} on {chain}: {e}",
        )


@tool()
async def evm_get_gas_price(
    chain: str = "ethereum",
) -> EvmGasPriceResponse:
    """
    Get the current gas price from an EVM-compatible blockchain.

    Returns the gas price in both wei and Gwei using JSON-RPC eth_gasPrice.
    Useful for estimating transaction costs before submitting transactions.
    Supports Ethereum, Polygon, Arbitrum, Optimism, and Base chains by default.

    Args:
        chain: Blockchain to query. Defaults to 'ethereum'. Supported chains:
               ethereum, polygon, arbitrum, optimism, base. Can also use a
               custom chain if EVM_RPC_URL is set.

    Returns:
        Current gas price in wei and Gwei, or error message.
    """
    try:
        env_url = await resolve_credential("EVM_RPC_URL")
        rpc_url = _get_rpc_url(chain, env_url)
        if not rpc_url:
            return EvmGasPriceResponse(
                success=False,
                error=f"No RPC URL configured for chain '{chain}'. "
                f"Set EVM_RPC_URL or use a supported chain: {', '.join(DEFAULT_RPC_URLS.keys())}",
            )

        logger.info("Fetching gas price on %s", chain)
        result = await _rpc_call(rpc_url, "eth_gasPrice", [])

        gas_price_hex = result.get("result", "0x0")
        gas_price_wei = int(gas_price_hex, 16)
        gas_price_gwei = gas_price_wei / 1e9

        return EvmGasPriceResponse(
            success=True,
            data=EvmGasPriceData(
                gas_price_wei=str(gas_price_wei),
                gas_price_gwei=f"{gas_price_gwei:.9f}",
                chain=chain,
            ),
        )
    except Exception as e:
        logger.exception("Failed to fetch gas price on %s", chain)
        return EvmGasPriceResponse(
            success=False,
            error=f"Error fetching gas price on {chain}: {e}",
        )
