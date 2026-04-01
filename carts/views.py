from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemCreateUpdateSerializer
from products.models import Product


def get_or_create_cart(user):
    """Get or create cart for authenticated user."""
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_list(request):
    """GET /cart/ - Retrieve user's cart."""
    cart = get_or_create_cart(request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_add_item(request):
    """POST /cart/items/ - Add item to cart."""
    serializer = CartItemCreateUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    cart = get_or_create_cart(request.user)
    product = Product.objects.get(id=serializer.validated_data['product_id'])
    quantity = serializer.validated_data['quantity']

    # Add or update cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'unit_price': product.price, 'quantity': quantity}
    )
    
    if not created:
        # If item exists, increase quantity
        cart_item.quantity += quantity
        cart_item.save()

    return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cart_update_item(request, item_id):
    """PATCH /cart/items/{itemId}/ - Update item quantity."""
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
    except CartItem.DoesNotExist:
        return Response(
            {'detail': 'Item not found in cart.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = CartItemCreateUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    cart_item.quantity = serializer.validated_data['quantity']
    cart_item.save()

    cart = cart_item.cart
    return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cart_delete_item(request, item_id):
    """DELETE /cart/items/{itemId}/ - Remove item from cart."""
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
    except CartItem.DoesNotExist:
        return Response(
            {'detail': 'Item not found in cart.'},
            status=status.HTTP_404_NOT_FOUND
        )

    cart = cart_item.cart
    cart_item.delete()

    return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_clear(request):
    """POST /cart/clear/ - Clear all items from cart."""
    cart = get_or_create_cart(request.user)
    cart.items.all().delete()
    return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)



# Create your views here.
