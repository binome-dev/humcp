---
name: ecommerce
description: Ecommerce tools for managing Shopify products and retrieving brand data. Use when the user needs to list, view, or create Shopify products, or look up brand assets like logos and colors.
---

# Ecommerce Tools

Tools for interacting with ecommerce platforms and brand data APIs.

## Available Tools

### Shopify (Required: SHOPIFY_STORE_URL, SHOPIFY_ACCESS_TOKEN)

- `shopify_list_products` - List products from a Shopify store
- `shopify_get_product` - Get a single product by ID
- `shopify_create_product` - Create a new product

### Brandfetch (Required: BRANDFETCH_API_KEY)

- `brandfetch_get_brand` - Get brand data (logos, colors, description) by domain

## Requirements

Set environment variables:
- `SHOPIFY_STORE_URL`: Your Shopify store URL (e.g., `https://my-store.myshopify.com`)
- `SHOPIFY_ACCESS_TOKEN`: Shopify Admin API access token
- `BRANDFETCH_API_KEY`: Brandfetch API key

## Examples

### List products

```python
result = await shopify_list_products(limit=10)
```

### Response format

```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": 1234567890,
        "title": "Example Product",
        "status": "active",
        "vendor": "My Store",
        "variants": [
          {
            "id": 9876543210,
            "title": "Default Title",
            "price": "29.99",
            "inventory_quantity": 100
          }
        ]
      }
    ],
    "count": 1
  }
}
```

### Create a product

```python
result = await shopify_create_product(
    title="New Widget",
    body_html="<p>A fantastic widget</p>",
    vendor="Widget Co"
)
```

### Get brand data

```python
result = await brandfetch_get_brand(domain="nike.com")
```

## When to Use

- Managing products in a Shopify store
- Listing or searching for products
- Creating new products programmatically
- Looking up brand assets (logos, colors, fonts)
- Getting company brand information for design or marketing
