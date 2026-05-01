from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.openapi import OpenApiTypes
from rest_framework import serializers


# ============ CART ENDPOINTS ============

cart_list_schema = extend_schema(
    summary="Get shopping cart",
    description="Retrieve user's shopping cart with all items and total price",
    responses={200: OpenApiTypes.OBJECT},
    tags=['Cart']
)

cart_add_item_schema = extend_schema(
    summary="Add item to cart",
    description="Add a product to the shopping cart",
    request={"type": "object", "properties": {
        "product_id": {"type": "string", "format": "uuid"},
        "stock_id": {"type": "string", "format": "uuid"},
        "quantity": {"type": "integer", "minimum": 1}
    }},
    responses={200: OpenApiTypes.OBJECT},
    tags=['Cart']
)

cart_remove_item_schema = extend_schema(
    summary="Remove item from cart",
    description="Remove a product from the shopping cart",
    request={"type": "object", "properties": {
        "product_id": {"type": "string", "format": "uuid"}
    }},
    responses={200: OpenApiTypes.OBJECT},
    tags=['Cart']
)

cart_clear_schema = extend_schema(
    summary="Clear cart",
    description="Remove all items from the shopping cart",
    responses={200: OpenApiTypes.OBJECT},
    tags=['Cart']
)


# ============ ORDER ENDPOINTS ============

order_list_schema = extend_schema(
    summary="List user's orders",
    description="Get all orders placed by the current user",
    responses={200: OpenApiTypes.OBJECT},
    tags=['Orders']
)

order_retrieve_schema = extend_schema(
    summary="Get order details",
    description="Retrieve full details of a specific order including items, vendors, and shipment",
    responses={200: OpenApiTypes.OBJECT},
    tags=['Orders']
)

order_checkout_schema = extend_schema(
    summary="Create order from cart",
    description="Convert shopping cart into an order with multi-vendor support",
    request={"type": "object", "properties": {
        "shipping_method": {"type": "string", "enum": ["pickup", "delivery"]},
        "station_id": {"type": "string", "format": "uuid", "nullable": True}
    }},
    responses={201: OpenApiTypes.OBJECT},
    tags=['Orders']
)

order_cancel_schema = extend_schema(
    summary="Cancel order",
    description="Cancel a pending or confirmed order and reverse all changes",
    request={"type": "object", "properties": {
        "reason": {"type": "string"}
    }},
    responses={200: OpenApiTypes.OBJECT},
    tags=['Orders']
)


# ============ VENDOR DASHBOARD ENDPOINTS ============

vendor_orders_schema = extend_schema(
    summary="Get vendor's orders",
    description="List all orders for the current vendor with their status and details",
    responses={200: OpenApiTypes.OBJECT},
    tags=['Vendor Dashboard']
)

vendor_wallet_schema = extend_schema(
    summary="Get vendor wallet",
    description="View vendor's available balance, pending balance, and earning totals",
    responses={200: OpenApiTypes.OBJECT},
    tags=['Vendor Dashboard']
)

vendor_payout_schema = extend_schema(
    summary="Request payout",
    description="Submit a payout request from available balance to specified payment method",
    request={"type": "object", "properties": {
        "amount": {"type": "number", "format": "decimal"},
        "payout_method": {"type": "string", "enum": ["mpesa", "bank_transfer"]}
    }},
    responses={201: OpenApiTypes.OBJECT},
    tags=['Vendor Dashboard']
)


# ============ PRODUCT BROWSE ENDPOINTS ============

product_browse_list_schema = extend_schema(
    summary="Browse products",
    description="List all products from verified vendors with optional filters",
    parameters=[
        {"name": "search", "in": "query", "schema": {"type": "string"}, "description": "Search by name"},
        {"name": "category_id", "in": "query", "schema": {"type": "string"}, "description": "Filter by category"},
        {"name": "min_price", "in": "query", "schema": {"type": "number"}, "description": "Minimum price"},
        {"name": "max_price", "in": "query", "schema": {"type": "number"}, "description": "Maximum price"},
        {"name": "page", "in": "query", "schema": {"type": "integer"}, "description": "Page number"},
    ],
    responses={200: OpenApiTypes.OBJECT},
    tags=['Products']
)

product_stock_options_schema = extend_schema(
    summary="Get stock options",
    description="Get available stock entries for a product (from different vendors with different prices)",
    responses={200: OpenApiTypes.OBJECT},
    tags=['Products']
)


# ============ VENDOR PRODUCT MANAGEMENT ENDPOINTS ============

vendor_product_list_schema = extend_schema(
    summary="List my products",
    description="List all products created by the current vendor",
    responses={200: OpenApiTypes.OBJECT},
    tags=['Vendor Products']
)

vendor_product_create_schema = extend_schema(
    summary="Create product",
    description="Create a new product for sale",
    request={"type": "object", "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "price": {"type": "number", "format": "decimal"},
        "stock_quantity": {"type": "integer"},
        "image_url": {"type": "string", "format": "uri"},
        "category": {"type": "string", "format": "uuid"},
        "is_active": {"type": "boolean"}
    }},
    responses={201: OpenApiTypes.OBJECT},
    tags=['Vendor Products']
)

vendor_product_toggle_active_schema = extend_schema(
    summary="Toggle product active status",
    description="Enable or disable a product from being listed",
    responses={200: OpenApiTypes.OBJECT},
    tags=['Vendor Products']
)

vendor_product_stock_schema = extend_schema(
    summary="Get product stock",
    description="View stock entries for a specific product",
    responses={200: OpenApiTypes.OBJECT},
    tags=['Vendor Products']
)

vendor_product_update_stock_schema = extend_schema(
    summary="Update product stock",
    description="Create or update stock quantity and price for a product",
    request={"type": "object", "properties": {
        "quantity": {"type": "integer", "minimum": 0},
        "price": {"type": "number", "format": "decimal", "minimum": 0}
    }},
    responses={200: OpenApiTypes.OBJECT},
    tags=['Vendor Products']
)

vendor_product_inventory_movements_schema = extend_schema(
    summary="Get inventory audit trail",
    description="View all inventory movements (sales, returns, adjustments) for a product",
    responses={200: OpenApiTypes.OBJECT},
    tags=['Vendor Products']
)
