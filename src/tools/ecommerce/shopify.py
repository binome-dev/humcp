"""Shopify Admin REST API tools for managing products."""

from __future__ import annotations

import logging

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.ecommerce.schemas import (
    ShopifyCreateProductData,
    ShopifyCreateProductResponse,
    ShopifyCustomer,
    ShopifyGetCustomersData,
    ShopifyGetCustomersResponse,
    ShopifyGetProductData,
    ShopifyGetProductResponse,
    ShopifyListOrdersData,
    ShopifyListOrdersResponse,
    ShopifyListProductsData,
    ShopifyListProductsResponse,
    ShopifyOrder,
    ShopifyProduct,
    ShopifyVariant,
)

logger = logging.getLogger("humcp.tools.shopify")

API_VERSION = "2024-01"


def _get_shopify_config(
    store_url: str | None, access_token: str | None
) -> tuple[str, str] | None:
    """Validate Shopify store URL and access token.

    Returns:
        A tuple of (store_url, access_token) or None if not configured.
    """
    if not store_url or not access_token:
        return None
    return store_url.rstrip("/"), access_token


def _parse_product(product: dict) -> ShopifyProduct:
    """Parse a Shopify product dict into a ShopifyProduct model.

    Args:
        product: Raw product dictionary from Shopify REST API.

    Returns:
        A ShopifyProduct instance.
    """
    variants = [
        ShopifyVariant(
            id=v.get("id", 0),
            title=v.get("title"),
            sku=v.get("sku"),
            price=v.get("price"),
            inventory_quantity=v.get("inventory_quantity"),
        )
        for v in product.get("variants", [])
    ]

    return ShopifyProduct(
        id=product.get("id", 0),
        title=product.get("title", ""),
        body_html=product.get("body_html"),
        vendor=product.get("vendor"),
        product_type=product.get("product_type"),
        status=product.get("status"),
        created_at=product.get("created_at"),
        updated_at=product.get("updated_at"),
        variants=variants,
    )


@tool()
async def shopify_list_products(limit: int = 50) -> ShopifyListProductsResponse:
    """
    List products from a Shopify store using the Admin REST API.

    Args:
        limit: Maximum number of products to return (1-250). Defaults to 50.

    Returns:
        List of products with their details and variants, or error message.
    """
    try:
        store_url_val = await resolve_credential("SHOPIFY_STORE_URL")
        access_token_val = await resolve_credential("SHOPIFY_ACCESS_TOKEN")
        config = _get_shopify_config(store_url_val, access_token_val)
        if not config:
            return ShopifyListProductsResponse(
                success=False,
                error="Shopify not configured. Set SHOPIFY_STORE_URL and SHOPIFY_ACCESS_TOKEN.",
            )

        store_url, access_token = config
        clamped_limit = max(1, min(limit, 250))

        logger.info("Listing products limit=%d", clamped_limit)

        url = f"{store_url}/admin/api/{API_VERSION}/products.json"
        headers = {"X-Shopify-Access-Token": access_token}
        params = {"limit": clamped_limit}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        raw_products = data.get("products", [])
        products = [_parse_product(p) for p in raw_products]

        return ShopifyListProductsResponse(
            success=True,
            data=ShopifyListProductsData(
                products=products,
                count=len(products),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error listing Shopify products")
        return ShopifyListProductsResponse(
            success=False,
            error=f"Shopify API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to list Shopify products")
        return ShopifyListProductsResponse(
            success=False,
            error=f"Error listing Shopify products: {e}",
        )


@tool()
async def shopify_get_product(product_id: str) -> ShopifyGetProductResponse:
    """
    Get a single product by its ID from a Shopify store.

    Args:
        product_id: The numeric Shopify product ID (e.g., '1234567890').

    Returns:
        Product details with variants, or error message.
    """
    try:
        store_url_val = await resolve_credential("SHOPIFY_STORE_URL")
        access_token_val = await resolve_credential("SHOPIFY_ACCESS_TOKEN")
        config = _get_shopify_config(store_url_val, access_token_val)
        if not config:
            return ShopifyGetProductResponse(
                success=False,
                error="Shopify not configured. Set SHOPIFY_STORE_URL and SHOPIFY_ACCESS_TOKEN.",
            )

        store_url, access_token = config

        logger.info("Fetching product %s", product_id)

        url = f"{store_url}/admin/api/{API_VERSION}/products/{product_id}.json"
        headers = {"X-Shopify-Access-Token": access_token}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

        raw_product = data.get("product")
        if not raw_product:
            return ShopifyGetProductResponse(
                success=False,
                error=f"Product not found: {product_id}",
            )

        product = _parse_product(raw_product)

        return ShopifyGetProductResponse(
            success=True,
            data=ShopifyGetProductData(product=product),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error fetching Shopify product %s", product_id)
        return ShopifyGetProductResponse(
            success=False,
            error=f"Shopify API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to fetch Shopify product %s", product_id)
        return ShopifyGetProductResponse(
            success=False,
            error=f"Error fetching Shopify product {product_id}: {e}",
        )


@tool()
async def shopify_create_product(
    title: str,
    body_html: str = "",
    vendor: str = "",
) -> ShopifyCreateProductResponse:
    """
    Create a new product in a Shopify store using the Admin REST API.

    Args:
        title: The product title (required).
        body_html: Product description in HTML format. Defaults to empty string.
        vendor: Product vendor name. Defaults to empty string.

    Returns:
        Created product details, or error message.
    """
    try:
        store_url_val = await resolve_credential("SHOPIFY_STORE_URL")
        access_token_val = await resolve_credential("SHOPIFY_ACCESS_TOKEN")
        config = _get_shopify_config(store_url_val, access_token_val)
        if not config:
            return ShopifyCreateProductResponse(
                success=False,
                error="Shopify not configured. Set SHOPIFY_STORE_URL and SHOPIFY_ACCESS_TOKEN.",
            )

        store_url, access_token = config

        if not title.strip():
            return ShopifyCreateProductResponse(
                success=False,
                error="Product title cannot be empty.",
            )

        logger.info("Creating product title=%s vendor=%s", title, vendor)

        url = f"{store_url}/admin/api/{API_VERSION}/products.json"
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }
        payload = {
            "product": {
                "title": title,
                "body_html": body_html,
                "vendor": vendor,
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        raw_product = data.get("product")
        if not raw_product:
            return ShopifyCreateProductResponse(
                success=False,
                error="Unexpected response: product not in response body.",
            )

        product = _parse_product(raw_product)

        return ShopifyCreateProductResponse(
            success=True,
            data=ShopifyCreateProductData(product=product),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error creating Shopify product")
        return ShopifyCreateProductResponse(
            success=False,
            error=f"Shopify API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to create Shopify product")
        return ShopifyCreateProductResponse(
            success=False,
            error=f"Error creating Shopify product: {e}",
        )


@tool()
async def shopify_list_orders(
    status: str = "any",
    limit: int = 10,
) -> ShopifyListOrdersResponse:
    """
    List orders from a Shopify store using the Admin REST API.

    Retrieves orders filtered by status. Each order includes its name, customer
    email, financial status, fulfillment status, total price, and line item count.

    Args:
        status: Order status filter. Valid values: 'open', 'closed', 'cancelled',
                'any'. Defaults to 'any' (returns all orders regardless of status).
        limit: Maximum number of orders to return (1-250). Defaults to 10.

    Returns:
        List of orders with their details, or error message.
    """
    try:
        store_url_val = await resolve_credential("SHOPIFY_STORE_URL")
        access_token_val = await resolve_credential("SHOPIFY_ACCESS_TOKEN")
        config = _get_shopify_config(store_url_val, access_token_val)
        if not config:
            return ShopifyListOrdersResponse(
                success=False,
                error="Shopify not configured. Set SHOPIFY_STORE_URL and SHOPIFY_ACCESS_TOKEN.",
            )

        store_url, access_token = config

        valid_statuses = {"open", "closed", "cancelled", "any"}
        if status not in valid_statuses:
            return ShopifyListOrdersResponse(
                success=False,
                error=f"Invalid status '{status}'. Valid statuses: {', '.join(sorted(valid_statuses))}",
            )

        clamped_limit = max(1, min(limit, 250))

        logger.info("Listing orders status=%s limit=%d", status, clamped_limit)

        url = f"{store_url}/admin/api/{API_VERSION}/orders.json"
        headers = {"X-Shopify-Access-Token": access_token}
        params: dict = {"limit": clamped_limit, "status": status}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        raw_orders = data.get("orders", [])
        orders = [
            ShopifyOrder(
                id=o.get("id", 0),
                name=o.get("name"),
                email=o.get("email"),
                financial_status=o.get("financial_status"),
                fulfillment_status=o.get("fulfillment_status"),
                total_price=o.get("total_price"),
                currency=o.get("currency"),
                created_at=o.get("created_at"),
                updated_at=o.get("updated_at"),
                line_items_count=len(o.get("line_items", [])),
            )
            for o in raw_orders
        ]

        return ShopifyListOrdersResponse(
            success=True,
            data=ShopifyListOrdersData(
                orders=orders,
                count=len(orders),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error listing Shopify orders")
        return ShopifyListOrdersResponse(
            success=False,
            error=f"Shopify API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to list Shopify orders")
        return ShopifyListOrdersResponse(
            success=False,
            error=f"Error listing Shopify orders: {e}",
        )


@tool()
async def shopify_get_customers(
    limit: int = 10,
) -> ShopifyGetCustomersResponse:
    """
    List customers from a Shopify store using the Admin REST API.

    Retrieves customer accounts with their contact information, order history
    summary, and account state. Useful for customer analytics and CRM workflows.

    Args:
        limit: Maximum number of customers to return (1-250). Defaults to 10.

    Returns:
        List of customers with their details, or error message.
    """
    try:
        store_url_val = await resolve_credential("SHOPIFY_STORE_URL")
        access_token_val = await resolve_credential("SHOPIFY_ACCESS_TOKEN")
        config = _get_shopify_config(store_url_val, access_token_val)
        if not config:
            return ShopifyGetCustomersResponse(
                success=False,
                error="Shopify not configured. Set SHOPIFY_STORE_URL and SHOPIFY_ACCESS_TOKEN.",
            )

        store_url, access_token = config
        clamped_limit = max(1, min(limit, 250))

        logger.info("Listing customers limit=%d", clamped_limit)

        url = f"{store_url}/admin/api/{API_VERSION}/customers.json"
        headers = {"X-Shopify-Access-Token": access_token}
        params = {"limit": clamped_limit}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        raw_customers = data.get("customers", [])
        customers = [
            ShopifyCustomer(
                id=c.get("id", 0),
                email=c.get("email"),
                first_name=c.get("first_name"),
                last_name=c.get("last_name"),
                orders_count=c.get("orders_count"),
                total_spent=c.get("total_spent"),
                state=c.get("state"),
                created_at=c.get("created_at"),
                updated_at=c.get("updated_at"),
            )
            for c in raw_customers
        ]

        return ShopifyGetCustomersResponse(
            success=True,
            data=ShopifyGetCustomersData(
                customers=customers,
                count=len(customers),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error listing Shopify customers")
        return ShopifyGetCustomersResponse(
            success=False,
            error=f"Shopify API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to list Shopify customers")
        return ShopifyGetCustomersResponse(
            success=False,
            error=f"Error listing Shopify customers: {e}",
        )
