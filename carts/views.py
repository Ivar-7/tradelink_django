from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import CartItemCreateUpdateSerializer
from .services import CartItemService, CartService
from products.services import ProductService


def _build_cart_payload(user_id):
    cart = CartService.get_or_create_cart(user_id)
    items = CartItemService.list_items(cart["cart_id"])
    total = CartService.update_total(cart["cart_id"])

    normalized_items = []
    for item in items:
        product = ProductService.get_product(item["stock_id"])
        unit_price = float(product.get("price", 0)) if product else 0
        quantity = int(item.get("quantity", 0))
        normalized_items.append(
            {
                "product_id": item.get("stock_id"),
                "product_name": product.get("product_name") if product else "",
                "product_image": product.get("image_url", "") if product else "",
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": unit_price * quantity,
                "cart_item_id": item.get("cart_item_id"),
            }
        )

    return {
        "id": cart.get("cart_id"),
        "user_id": cart.get("user_id"),
        "date_created": cart.get("date_created"),
        "total_price": float(total),
        "products": normalized_items,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_list(request):
    """GET /cart/ - Retrieve user's cart."""
    return Response(_build_cart_payload(str(request.user.id)))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_add_item(request):
    """POST /cart/items/ - Add item to cart."""
    serializer = CartItemCreateUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user_id = str(request.user.id)
    cart = CartService.get_or_create_cart(user_id)
    product = ProductService.get_product(serializer.validated_data['product_id'])
    quantity = serializer.validated_data['quantity']

    if not product:
        return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

    CartItemService.add_or_increment_item(
        cart_id=cart['cart_id'],
        stock_id=serializer.validated_data['product_id'],
        quantity=quantity,
        unit_price=product.get('price', 0),
    )

    return Response(_build_cart_payload(user_id), status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cart_update_item(request, item_id):
    """PATCH /cart/items/{itemId}/ - Update item quantity."""
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

    return Response(_build_cart_payload(str(request.user.id)), status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cart_delete_item(request, item_id):
    """DELETE /cart/items/{itemId}/ - Remove item from cart."""
    existing = CartItemService.get_item(item_id)
    if not existing:
        return Response(
            {'detail': 'Item not found in cart.'},
            status=status.HTTP_404_NOT_FOUND
        )

    CartItemService.delete_item(item_id)
    return Response(_build_cart_payload(str(request.user.id)), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_clear(request):
    """POST /cart/clear/ - Clear all items from cart."""
    user_id = str(request.user.id)
    cart = CartService.get_or_create_cart(user_id)
    CartItemService.clear(cart['cart_id'])
    return Response(_build_cart_payload(user_id), status=status.HTTP_200_OK)



# Create your views here.
