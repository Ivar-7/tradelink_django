import logging
from datetime import datetime
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from carts.models import Cart
from .models import (
    Order, OrderItem, DeliveryAddress, OrderIssueReport, ReturnRequest,
    OrderStatus, ReturnStatus
)
from .serializers import (
    OrderSerializer, OrderListSerializer, OrderCreateSerializer,
    OrderCancelSerializer, OrderIssueCreateSerializer, 
    ReturnRequestCreateSerializer, DeliveryAddressSerializer
)

logger = logging.getLogger(__name__)


class OrderViewSet(viewsets.ModelViewSet):
    """
    API for managing orders.
    
    Endpoints:
    - GET /orders/ - List user's orders
    - GET /orders/{id}/ - Get order detail
    - POST /orders/ - Create new order (checkout)
    - POST /orders/{id}/confirm/ - Confirm delivery
    - POST /orders/{id}/cancel/ - Cancel order
    - POST /orders/{id}/issue/ - Report order issue
    - POST /orders/{id}/return/ - Request return
    """
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']
    ordering = ['-order_date']

    def get_queryset(self):
        """Only show orders for the authenticated user (unless admin)."""
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use appropriate serializer for each action."""
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'cancel':
            return OrderCancelSerializer
        elif self.action == 'report_issue':
            return OrderIssueCreateSerializer
        elif self.action == 'request_return':
            return ReturnRequestCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        """Create a new order from cart or provided products."""
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get cart to calculate total
        cart = Cart.objects.filter(user=request.user).first()
        
        # Use provided products or cart items
        items_data = serializer.validated_data.get('products')
        if items_data:
            # Create items from provided data
            total_amount = 0
            items_to_create = []
            for item_data in items_data:
                product_id = item_data['product_id']
                quantity = item_data['quantity']
                from products.models import Product
                product = Product.objects.get(id=product_id)
                subtotal = product.price * quantity
                total_amount += subtotal
                items_to_create.append({
                    'product': product,
                    'product_name': product.name,
                    'product_image': product.image_url or '',
                    'quantity': quantity,
                    'unit_price': product.price,
                })
        elif cart and cart.items.exists():
            # Create from cart
            total_amount = cart.total_price
            items_to_create = [
                {
                    'product': item.product,
                    'product_name': item.product_name,
                    'product_image': item.product_image,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                }
                for item in cart.items.all()
            ]
        else:
            return Response(
                {'detail': 'No items to order.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create order
        order = Order.objects.create(
            user=request.user,
            order_amount=total_amount,
            shipping_method=serializer.validated_data['shipping_method'],
            status=OrderStatus.PENDING
        )

        # Create order items
        for item_data in items_to_create:
            OrderItem.objects.create(order=order, **item_data)

        # Create delivery address if provided
        address_data = serializer.validated_data.get('delivery_address')
        if address_data:
            DeliveryAddress.objects.create(order=order, **address_data)

        # Clear cart after order creation
        if cart:
            cart.items.all().delete()

        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """POST /orders/{id}/confirm/ - Confirm delivery."""
        order = self.get_object()
        
        if order.status == OrderStatus.CANCELLED:
            return Response(
                {'detail': 'Cannot confirm a cancelled order.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = OrderStatus.DELIVERED
        order.delivered_at = timezone.now()
        order.save()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """POST /orders/{id}/cancel/ - Cancel order."""
        order = self.get_object()

        if order.status == OrderStatus.CANCELLED:
            return Response(
                {'detail': 'Order is already cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            return Response(
                {'detail': f'Cannot cancel order with status {order.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order.status = OrderStatus.CANCELLED
        order.cancelled_at = timezone.now()
        order.cancellation_reason = serializer.validated_data['reason']
        order.save()

        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        """POST /orders/{id}/issue/ - Report order issue."""
        order = self.get_object()

        # Check if issue already exists
        if hasattr(order, 'issue_report'):
            return Response(
                {'detail': 'Issue already reported for this order.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OrderIssueCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        OrderIssueReport.objects.create(
            order=order,
            type=serializer.validated_data['type'],
            details=serializer.validated_data['details']
        )

        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def request_return(self, request, pk=None):
        """POST /orders/{id}/return/ - Request return."""
        order = self.get_object()

        # Check if return already exists
        if hasattr(order, 'return_request'):
            return Response(
                {'detail': 'Return already requested for this order.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReturnRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return_request = ReturnRequest.objects.create(
            order=order,
            reason=serializer.validated_data['reason'],
            notes=serializer.validated_data.get('notes', ''),
            requested_at=timezone.now()
        )

        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        """List orders with optional filtering by status."""
        # Handle 'all' and status aliases from frontend
        status_filter = request.query_params.get('status')
        queryset = self.get_queryset()

        if status_filter and status_filter != 'all':
            # Map frontend status aliases to backend values
            status_map = {
                'processing': OrderStatus.CONFIRMED,
                'returns': OrderStatus.PENDING,  # Simplified for now
            }
            mapped_status = status_map.get(status_filter, status_filter)
            queryset = queryset.filter(status=mapped_status)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'orders': serializer.data,
            'total': queryset.count()
        })


# Create your views here.
