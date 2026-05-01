from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from decimal import Decimal
from drf_spectacular.utils import extend_schema

from users.models import VendorProfile
from carts.models import Cart
from products.models import Product, Stock
from .models import Order, OrderItem, OrderSuborder, Shipment, OrderStatus, OrderStatusHistory
from payments.models import VendorWallet, VendorPayout
from .serializers import (
    OrderSerializer, OrderListSerializer, OrderItemSerializer,
    OrderSuborderSerializer, ShipmentSerializer, OrderStatusHistorySerializer
)
from .services import OrderService
from carts.services_django import CartService
from payments.serializers import VendorWalletSerializer, VendorPayoutSerializer, VendorPayoutRequestSerializer
from products.serializers import ProductListSerializer, ProductSerializer


class ShipmentTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """Public shipment tracking lookup by tracking number."""
    permission_classes = [permissions.AllowAny]
    queryset = Shipment.objects.select_related('order', 'order__user').all()
    lookup_field = 'tracking_number'

    def get_serializer_class(self):
        return ShipmentSerializer

    def retrieve(self, request, *args, **kwargs):
        shipment = self.get_object()
        return Response(ShipmentSerializer(shipment).data)


class ProductBrowseViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse products from verified vendors."""
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Only show products from verified vendors that are active."""
        return Product.objects.filter(
            is_active=True,
            vendor__vendorprofile__is_verified=True,
            vendor__vendorprofile__is_suspended=False
        ).select_related('vendor', 'category').prefetch_related('reviews')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductSerializer
        return ProductListSerializer

    @extend_schema(description="Get available stock options for a product")
    @action(detail=True, methods=['get'])
    def stock_options(self, request, pk=None):
        try:
            product = self.get_object()
            stocks = Stock.objects.filter(
                product=product,
                vendor__vendorprofile__is_verified=True,
                vendor__vendorprofile__is_suspended=False,
                quantity__gt=0,
            ).select_related('vendor')
            return Response([
                {
                    'id': str(stock.id),
                    'product_id': str(stock.product.id),
                    'product_name': stock.product.name,
                    'vendor_id': str(stock.vendor.id),
                    'vendor_name': stock.vendor.username,
                    'quantity': stock.quantity,
                    'available_quantity': stock.available_quantity,
                    'reserved_quantity': stock.reserved_quantity,
                    'price': str(stock.price),
                    'discounted_price': str(stock.discounted_price),
                    'is_flash_sale': stock.is_flash_sale,
                    'discount_percentage': str(stock.discount_percentage),
                    'created_at': stock.created_at,
                }
                for stock in stocks
            ])
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)


class CartViewSet(viewsets.ViewSet):
    """Cart management."""
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(description="Get user's shopping cart")
    def list(self, request):
        """Get user's cart with items."""
        try:
            cart = request.user.cart
            items = cart.items.select_related('product__vendor').all()
            return Response({
                'id': str(cart.id),
                'total_price': str(cart.total_price),
                'items': [{
                    'id': str(item.id),
                    'product_id': str(item.product.id),
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'unit_price': str(item.unit_price),
                    'subtotal': str(item.subtotal),
                    'vendor_id': str(item.product.vendor.id),
                    'vendor_name': item.product.vendor.username,
                } for item in items]
            })
        except Cart.DoesNotExist:
            return Response({'items': [], 'total_price': '0.00'})
    
    @extend_schema(description="Add item to cart")
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add product to cart."""
        product_id = request.data.get('product_id')
        stock_id = request.data.get('stock_id')
        quantity = request.data.get('quantity', 1)
        
        try:
            item = CartService.add_to_cart(
                request.user, product_id, stock_id, int(quantity)
            )
            return Response({
                'message': 'Item added to cart',
                'product_id': str(item.product.id),
                'quantity': item.quantity
            })
        except (Product.DoesNotExist, Stock.DoesNotExist) as e:
            raise ValidationError(f'Product not found: {str(e)}')
        except ValueError as e:
            raise ValidationError(str(e))
    
    @extend_schema(description="Remove item from cart")
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """Remove product from cart."""
        product_id = request.data.get('product_id')
        CartService.remove_from_cart(request.user, product_id)
        return Response({'message': 'Item removed from cart'})
    
    @extend_schema(description="Clear entire cart")
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear all items from cart."""
        CartService.clear_cart(request.user)
        return Response({'message': 'Cart cleared'})


class OrderViewSet(viewsets.ViewSet):
    """Order management for buyers."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_order_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related(
            'user', 'shipment', 'delivery_address'
        ).prefetch_related('items__vendor', 'suborders__vendor', 'status_history__changed_by')
    
    @extend_schema(description="List user's orders")
    def list(self, request):
        """List all orders for current user."""
        orders = self.get_order_queryset().order_by('-order_date')
        return Response(OrderListSerializer(orders, many=True).data)
    
    @extend_schema(description="Get order details")
    def retrieve(self, request, pk=None):
        """Get order details with items and suborders."""
        try:
            order = self.get_order_queryset().get(id=pk)
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(description="Get order tracking timeline")
    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        try:
            order = self.get_order_queryset().get(id=pk)
            return Response({
                'order_id': str(order.id),
                'status': order.status,
                'tracking_number': order.tracking_number,
                'shipment': ShipmentSerializer(order.shipment).data if hasattr(order, 'shipment') else None,
                'timeline': OrderStatusHistorySerializer(order.status_history.all(), many=True).data,
            })
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(description="Create order from cart")
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """Create order from cart during checkout."""
        try:
            cart = request.user.cart
            shipping_method = request.data.get('shipping_method')
            station_id = request.data.get('station_id')
            
            if not shipping_method:
                raise ValidationError('shipping_method is required')
            
            # Create order from cart
            order = OrderService.create_order_from_cart(
                request.user, cart, None, shipping_method, station_id
            )
            OrderService.record_status_change(order, 'created', order.status, request.user, 'buyer', 'Order placed')
            
            # Clear cart
            CartService.clear_cart(request.user)
            
            return Response({
                'message': 'Order created successfully',
                'order_id': str(order.id),
                'order_amount': str(order.order_amount),
                'status': order.status,
            }, status=status.HTTP_201_CREATED)
        except Cart.DoesNotExist:
            raise ValidationError('Cart not found')
        except ValueError as e:
            raise ValidationError(str(e))
    
    @extend_schema(description="Cancel order")
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order."""
        try:
            order = Order.objects.get(id=pk, user=request.user)
            reason = request.data.get('reason', '')
            
            OrderService.cancel_order(order, changed_by=request.user, reason=reason)
            
            return Response({
                'message': 'Order cancelled successfully',
                'order_id': str(order.id),
                'status': order.status,
            })
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            raise ValidationError(str(e))

    @extend_schema(description="Buyer confirms delivery")
    @action(detail=True, methods=['post'])
    def confirm_delivery(self, request, pk=None):
        try:
            order = self.get_order_queryset().get(id=pk)
            OrderService.mark_order_delivered(order, changed_by=request.user, notes='Buyer confirmed delivery')
            return Response({'message': 'Delivery confirmed', 'order_id': str(order.id), 'status': order.status})
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            raise ValidationError(str(e))


class VendorDashboardViewSet(viewsets.ViewSet):
    """Vendor dashboard for viewing their orders."""
    permission_classes = [permissions.IsAuthenticated]
    
    def _is_vendor(self, user):
        """Check if user is a vendor."""
        return hasattr(user, 'vendorprofile') and user.vendorprofile is not None
    
    @extend_schema(description="Get vendor's orders")
    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """Get all orders for current vendor."""
        if not self._is_vendor(request.user):
            return Response(
                {'error': 'User is not a vendor'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all suborders for this vendor
        suborders = OrderSuborder.objects.filter(
            vendor=request.user
        ).select_related('order', 'order__user', 'order__shipment').prefetch_related(
            'order__items', 'status_history__changed_by'
        ).order_by('-created_at')
        
        return Response([{
            'order_id': str(suborder.order.id),
            'order_date': suborder.order.order_date.isoformat(),
            'buyer_email': suborder.order.user.email,
            'subtotal': str(suborder.subtotal),
            'status': suborder.status,
            'items_count': suborder.order.items.filter(vendor=request.user).count(),
            'created_at': suborder.created_at.isoformat(),
            'tracking_number': suborder.order.tracking_number,
            'shipment_status': suborder.order.shipment.status if hasattr(suborder.order, 'shipment') else None,
        } for suborder in suborders])

    @extend_schema(description="Vendor accepts a suborder")
    @action(detail=False, methods=['put'], url_path='orders/(?P<order_id>[^/.]+)/accept')
    def accept_order(self, request, order_id=None):
        try:
            suborder = OrderSuborder.objects.select_related('order').get(order_id=order_id, vendor=request.user)
            old_status = suborder.status
            suborder.status = OrderStatus.PROCESSING
            suborder.save(update_fields=['status', 'updated_at'])
            OrderService.record_status_change(suborder.order, old_status, suborder.status, request.user, 'vendor', 'Vendor accepted order', suborder=suborder)
            return Response({'message': 'Order accepted', 'order_id': str(suborder.order.id), 'status': suborder.status})
        except OrderSuborder.DoesNotExist:
            return Response({'error': 'Suborder not found'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(description="Vendor marks suborder as shipped")
    @action(detail=False, methods=['put'], url_path='orders/(?P<order_id>[^/.]+)/ship')
    def ship_order(self, request, order_id=None):
        try:
            suborder = OrderSuborder.objects.select_related('order').get(order_id=order_id, vendor=request.user)
            tracking_number = request.data.get('tracking_number') or f'TRK-{suborder.order.id.hex[:8].upper()}'
            delivery_fee = request.data.get('delivery_fee', '0.00')
            if not tracking_number:
                raise ValidationError('tracking_number is required')
            OrderService.mark_order_shipped(suborder.order, tracking_number, Decimal(str(delivery_fee)), changed_by=request.user, changed_by_role='vendor')
            return Response({'message': 'Order shipped', 'order_id': str(suborder.order.id), 'tracking_number': tracking_number})
        except OrderSuborder.DoesNotExist:
            return Response({'error': 'Suborder not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            raise ValidationError(str(e))

    @extend_schema(description="Vendor rejects a suborder")
    @action(detail=False, methods=['put'], url_path='orders/(?P<order_id>[^/.]+)/reject')
    def reject_order(self, request, order_id=None):
        try:
            suborder = OrderSuborder.objects.select_related('order').get(order_id=order_id, vendor=request.user)
            reason = request.data.get('reason', 'Rejected by vendor')
            old_status = suborder.status
            suborder.status = OrderStatus.CANCELLED
            suborder.save(update_fields=['status', 'updated_at'])
            OrderService.record_status_change(suborder.order, old_status, suborder.status, request.user, 'vendor', reason, suborder=suborder)
            return Response({'message': 'Order rejected', 'order_id': str(suborder.order.id), 'status': suborder.status})
        except OrderSuborder.DoesNotExist:
            return Response({'error': 'Suborder not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(description="Get vendor's wallet")
    @action(detail=False, methods=['get'])
    def wallet(self, request):
        """Get vendor's wallet information."""
        if not self._is_vendor(request.user):
            return Response(
                {'error': 'User is not a vendor'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            wallet = request.user.vendor_wallet
        except VendorWallet.DoesNotExist:
            wallet = VendorWallet.objects.create(vendor=request.user)
        
        serializer = VendorWalletSerializer(wallet)
        return Response(serializer.data)
    
    @extend_schema(description="Request payout")
    @action(detail=False, methods=['post'])
    def request_payout(self, request):
        """Request payout from wallet."""
        if not self._is_vendor(request.user):
            return Response(
                {'error': 'User is not a vendor'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = VendorPayoutRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            wallet = request.user.vendor_wallet
            amount = serializer.validated_data['amount']
            
            if wallet.available_balance < amount:
                raise ValidationError('Insufficient available balance')
            
            # Create payout record
            payout = VendorPayout.objects.create(
                vendor=request.user,
                amount=amount,
                payout_method=serializer.validated_data['payout_method'],
                status='pending'
            )
            
            # Deduct from wallet
            wallet.available_balance -= amount
            wallet.total_withdrawn += amount
            wallet.save()
            
            return Response({
                'message': 'Payout request submitted',
                'payout_id': str(payout.id),
                'amount': str(amount),
            }, status=status.HTTP_201_CREATED)
        except VendorWallet.DoesNotExist:
            raise ValidationError('Vendor wallet not found')


class AdminOrderViewSet(viewsets.ViewSet):
    """Admin order dashboard and status control."""
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Order.objects.select_related('user', 'shipment', 'delivery_address').prefetch_related('items__vendor', 'suborders__vendor', 'status_history__changed_by')

    @extend_schema(description="List all orders for admin")
    def list(self, request):
        orders = self.get_queryset().order_by('-order_date')
        return Response(OrderListSerializer(orders, many=True).data)

    @extend_schema(description="Get any order details")
    def retrieve(self, request, pk=None):
        try:
            order = self.get_queryset().get(id=pk)
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(description="Update order status")
    @action(detail=True, methods=['put'])
    def status(self, request, pk=None):
        try:
            order = self.get_queryset().get(id=pk)
            new_status = request.data.get('status')
            notes = request.data.get('notes', '')
            if new_status not in dict(OrderStatus.choices):
                raise ValidationError('Invalid status')
            old_status = order.status
            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])
            OrderService.record_status_change(order, old_status, new_status, request.user, 'admin', notes)
            if hasattr(order, 'shipment') and new_status == OrderStatus.OUT_FOR_DELIVERY:
                order.shipment.status = 'in_transit'
                order.shipment.save(update_fields=['status', 'last_update_time'])
            return Response({'message': 'Order status updated', 'order_id': str(order.id), 'status': order.status})
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError:
            raise

    @extend_schema(description="Assign courier / mark order out for delivery")
    @action(detail=True, methods=['put'])
    def assign_courier(self, request, pk=None):
        try:
            order = self.get_queryset().get(id=pk)
            notes = request.data.get('notes', 'Courier assigned')
            OrderService.mark_order_out_for_delivery(order, changed_by=request.user, notes=notes)
            return Response({'message': 'Courier assigned', 'order_id': str(order.id), 'status': order.status})
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
