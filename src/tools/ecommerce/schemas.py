"""Pydantic output schemas for ecommerce tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# Shopify Schemas
# =============================================================================


class ShopifyVariant(BaseModel):
    """A single product variant from Shopify."""

    id: int = Field(..., description="Variant ID")
    title: str | None = Field(None, description="Variant title")
    sku: str | None = Field(None, description="Variant SKU")
    price: str | None = Field(None, description="Variant price")
    inventory_quantity: int | None = Field(None, description="Inventory quantity")


class ShopifyProduct(BaseModel):
    """A single product from Shopify."""

    id: int = Field(..., description="Product ID")
    title: str = Field(..., description="Product title")
    body_html: str | None = Field(None, description="Product description HTML")
    vendor: str | None = Field(None, description="Product vendor")
    product_type: str | None = Field(None, description="Product type")
    status: str | None = Field(
        None, description="Product status (active/draft/archived)"
    )
    created_at: str | None = Field(None, description="Creation timestamp")
    updated_at: str | None = Field(None, description="Last update timestamp")
    variants: list[ShopifyVariant] = Field(
        default_factory=list, description="Product variants"
    )


class ShopifyListProductsData(BaseModel):
    """Output data for shopify_list_products tool."""

    products: list[ShopifyProduct] = Field(
        default_factory=list, description="List of products"
    )
    count: int = Field(0, description="Number of products returned")


class ShopifyGetProductData(BaseModel):
    """Output data for shopify_get_product tool."""

    product: ShopifyProduct = Field(..., description="Product details")


class ShopifyCreateProductData(BaseModel):
    """Output data for shopify_create_product tool."""

    product: ShopifyProduct = Field(..., description="Created product details")


class ShopifyOrder(BaseModel):
    """A single order from Shopify."""

    id: int = Field(..., description="Order ID")
    name: str | None = Field(None, description="Order name (e.g., '#1001')")
    email: str | None = Field(None, description="Customer email")
    financial_status: str | None = Field(
        None, description="Payment status (paid/pending/refunded)"
    )
    fulfillment_status: str | None = Field(
        None, description="Fulfillment status (fulfilled/unfulfilled/partial)"
    )
    total_price: str | None = Field(None, description="Total order price")
    currency: str | None = Field(None, description="Currency code")
    created_at: str | None = Field(None, description="Order creation timestamp")
    updated_at: str | None = Field(None, description="Last update timestamp")
    line_items_count: int = Field(0, description="Number of line items")


class ShopifyListOrdersData(BaseModel):
    """Output data for shopify_list_orders tool."""

    orders: list[ShopifyOrder] = Field(
        default_factory=list, description="List of orders"
    )
    count: int = Field(0, description="Number of orders returned")


class ShopifyCustomer(BaseModel):
    """A single customer from Shopify."""

    id: int = Field(..., description="Customer ID")
    email: str | None = Field(None, description="Customer email address")
    first_name: str | None = Field(None, description="Customer first name")
    last_name: str | None = Field(None, description="Customer last name")
    orders_count: int | None = Field(None, description="Number of orders placed")
    total_spent: str | None = Field(None, description="Total amount spent")
    state: str | None = Field(
        None, description="Customer account state (enabled/disabled/invited)"
    )
    created_at: str | None = Field(None, description="Account creation timestamp")
    updated_at: str | None = Field(None, description="Last update timestamp")


class ShopifyGetCustomersData(BaseModel):
    """Output data for shopify_get_customers tool."""

    customers: list[ShopifyCustomer] = Field(
        default_factory=list, description="List of customers"
    )
    count: int = Field(0, description="Number of customers returned")


# =============================================================================
# Brandfetch Schemas
# =============================================================================


class BrandfetchLogo(BaseModel):
    """A brand logo from Brandfetch."""

    type: str | None = Field(None, description="Logo type (e.g., 'logo', 'icon')")
    theme: str | None = Field(None, description="Logo theme (e.g., 'light', 'dark')")
    formats: list[dict] = Field(
        default_factory=list, description="Available logo formats with URLs"
    )


class BrandfetchColor(BaseModel):
    """A brand color from Brandfetch."""

    hex: str | None = Field(None, description="Hex color code")
    type: str | None = Field(None, description="Color type (e.g., 'accent', 'brand')")
    brightness: int | None = Field(None, description="Color brightness value")


class BrandfetchBrandData(BaseModel):
    """Output data for brandfetch_get_brand tool."""

    name: str | None = Field(None, description="Brand name")
    domain: str | None = Field(None, description="Brand domain")
    description: str | None = Field(None, description="Brand description")
    long_description: str | None = Field(None, description="Detailed brand description")
    logos: list[BrandfetchLogo] = Field(default_factory=list, description="Brand logos")
    colors: list[BrandfetchColor] = Field(
        default_factory=list, description="Brand colors"
    )
    links: list[dict] = Field(
        default_factory=list, description="Brand social and web links"
    )
    company: dict | None = Field(None, description="Company information")


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class ShopifyListProductsResponse(ToolResponse[ShopifyListProductsData]):
    """Response schema for shopify_list_products tool."""

    pass


class ShopifyGetProductResponse(ToolResponse[ShopifyGetProductData]):
    """Response schema for shopify_get_product tool."""

    pass


class ShopifyCreateProductResponse(ToolResponse[ShopifyCreateProductData]):
    """Response schema for shopify_create_product tool."""

    pass


class ShopifyListOrdersResponse(ToolResponse[ShopifyListOrdersData]):
    """Response schema for shopify_list_orders tool."""

    pass


class ShopifyGetCustomersResponse(ToolResponse[ShopifyGetCustomersData]):
    """Response schema for shopify_get_customers tool."""

    pass


class BrandfetchBrandResponse(ToolResponse[BrandfetchBrandData]):
    """Response schema for brandfetch_get_brand tool."""

    pass
