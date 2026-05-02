import httpx
import time
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tradelink_django.supabase_postgrest import SupabaseAPIError

from .serializers import CartItemCreateUpdateSerializer
from .services import CartItemService, CartService
from products.services import ProductService


def _upstream_error_response(exc):
    if isinstance(exc, SupabaseAPIError):
        return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
    return Response(
        {'detail': 'Upstream cart service unavailable. Please retry.'},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def _run_with_upstream_retry(callback, retries=2, base_delay=0.2):
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return callback()
        except (SupabaseAPIError, httpx.HTTPError) as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(base_delay * (attempt + 1))
                continue
            raise

    raise last_exc


def _build_cart_payload(user, refresh_total=False):
    cart = CartService.get_or_create_cart(user)
    items = CartItemService.list_items(cart["cart_id"])

    normalized_items = []
    calculated_total = 0.0
    lookup_failed = False

    for item in items:
        product = None
        try:
            product = ProductService.get_product_for_stock(item["stock_id"])
        except (SupabaseAPIError, httpx.HTTPError):
            # Keep cart readable even when product enrichment is temporarily unavailable.
            lookup_failed = True

        unit_price = float(product.get("price", 0)) if product else 0.0
        quantity = int(item.get("quantity", 0))
        subtotal = unit_price * quantity
        calculated_total += subtotal

        normalized_items.append(
            {
                "product_id": product.get("product_id") if product else None,
                "stock_id": item.get("stock_id"),
                "product_name": product.get("product_name") if product else "",
                "product_image": product.get("image_url", "") if product else "",
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
                "cart_item_id": item.get("cart_item_id"),
            }
        )

    total_price = float(cart.get("total_price") or 0)
    if not lookup_failed:
        total_price = calculated_total
        if refresh_total:
            try:
                CartService.set_total(cart["cart_id"], total_price)
            except (SupabaseAPIError, httpx.HTTPError):
                # Do not fail request when persisting total is temporarily unavailable.
                pass

    return {
        "id": cart.get("cart_id"),
        "user_id": cart.get("user_id"),
        "date_created": cart.get("date_created"),
        "total_price": float(total_price),
        "products": normalized_items,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_list(request):
    """GET /cart/ - Retrieve user's cart."""
    try:
        payload = _run_with_upstream_retry(
            lambda: _build_cart_payload(request.user),
            retries=4,
            base_delay=0.25,
        )
        return Response(payload)
    except (SupabaseAPIError, httpx.HTTPError) as exc:
        return _upstream_error_response(exc)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_add_item(request):
    """POST /cart/items/ - Add item to cart."""
    serializer = CartItemCreateUpdateSerializer(data=request.data)
    try:
        serializer.is_valid(raise_exception=True)
    except (SupabaseAPIError, httpx.HTTPError) as exc:
        return _upstream_error_response(exc)

    quantity = serializer.validated_data['quantity']

    def _add_item_flow():
        cart = CartService.get_or_create_cart(request.user)
        stock_id = ProductService.resolve_stock_id(serializer.validated_data['product_id'])
        product = ProductService.get_product_for_stock(stock_id) if stock_id else None

        if not stock_id or not product:
            return None

        CartItemService.add_or_increment_item(
            cart_id=cart['cart_id'],
            stock_id=stock_id,
            quantity=quantity,
            unit_price=product.get('price', 0),
        )
        return _build_cart_payload(request.user, refresh_total=True)

    try:
        payload = _run_with_upstream_retry(_add_item_flow, retries=2, base_delay=0.2)
    except (SupabaseAPIError, httpx.HTTPError) as exc:
        return _upstream_error_response(exc)

    if payload is None:
        return Response({'detail': 'Product stock not found.'}, status=status.HTTP_404_NOT_FOUND)

    return Response(payload, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cart_update_item(request, item_id):
    """PATCH /cart/items/{itemId}/ - Update item quantity."""
    try:
        cart_item = CartItemService.get_item(item_id)
        if not cart_item:
            return Response(
                {'detail': 'Item not found in cart.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CartItemCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = CartItemService.update_quantity(item_id, serializer.validated_data['quantity'])
        if not updated:
            return Response({'detail': 'Item not found in cart.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(_build_cart_payload(request.user, refresh_total=True), status=status.HTTP_200_OK)
    except (SupabaseAPIError, httpx.HTTPError) as exc:
        return _upstream_error_response(exc)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cart_delete_item(request, item_id):
    """DELETE /cart/items/{itemId}/ - Remove item from cart."""
    try:
        existing = CartItemService.get_item(item_id)
        if not existing:
            return Response(
                {'detail': 'Item not found in cart.'},
                status=status.HTTP_404_NOT_FOUND
            )

        CartItemService.delete_item(item_id)
        return Response(_build_cart_payload(request.user, refresh_total=True), status=status.HTTP_200_OK)
    except (SupabaseAPIError, httpx.HTTPError) as exc:
        return _upstream_error_response(exc)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_clear(request):
    """POST /cart/clear/ - Clear all items from cart."""
    try:
        cart = CartService.get_or_create_cart(request.user)
        CartItemService.clear(cart['cart_id'])
        return Response(_build_cart_payload(request.user, refresh_total=True), status=status.HTTP_200_OK)
    except (SupabaseAPIError, httpx.HTTPError) as exc:
        return _upstream_error_response(exc)



# Create your views here.
