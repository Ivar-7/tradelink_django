from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from products.models import Stock, InventoryMovement
from payments.models import VendorWallet, VendorPayout
from .models import Order, OrderItem, OrderSuborder, Shipment, OrderStatus, OrderStatusHistory
import uuid


class OrderService:
    """Service for order processing operations."""

    @staticmethod
    def record_status_change(order, old_status, new_status, changed_by, changed_by_role, notes='', location='', suborder=None):
        """Persist an order status transition for tracking timelines."""
        return OrderStatusHistory.objects.create(
            order=order,
            suborder=suborder,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            changed_by_role=changed_by_role,
            notes=notes,
            location=location,
        )
    
    @staticmethod
    @transaction.atomic
    def create_order_from_cart(user, cart, address, shipping_method, station_id=None):
        """
        Create order from shopping cart.
        
        Creates master order, order items (with vendor_id), order suborders (per vendor),
        reserves stock, and credits vendor wallets.
        
        Args:
            user: Buyer user
            cart: Cart instance
            address: DeliveryAddress instance
            shipping_method: 'pickup' or 'delivery'
            station_id: Optional pickup station UUID
            
        Returns:
            Order instance
            
        Raises:
            ValueError: If cart is empty or stock issues
        """
        if not cart.items.exists():
            raise ValueError('Cart is empty')
        
        # Calculate order total
        total_amount = cart.total_price
        
        # Create master order
        order = Order.objects.create(
            user=user,
            order_amount=total_amount,
            shipping_method=shipping_method,
            status='pending'
        )
        
        # Group cart items by vendor
        vendors_map = {}
        
        for cart_item in cart.items.all():
            product = cart_item.product
            stock = product.stock_entries.first()  # Get first stock entry
            
            if not stock or stock.available_quantity < cart_item.quantity:
                raise ValueError(
                    f'Insufficient stock for {product.name}'
                )
            
            vendor = stock.vendor
            vendor_id = str(vendor.id)
            
            if vendor_id not in vendors_map:
                vendors_map[vendor_id] = {
                    'vendor': vendor,
                    'items': [],
                    'subtotal': Decimal('0.00')
                }
            
            # Create order item with vendor_id (THE GLUE)
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_image=product.image_url,
                quantity=cart_item.quantity,
                unit_price=stock.price,
                vendor=vendor  # THE GLUE - identify seller
            )
            
            subtotal = order_item.subtotal
            vendors_map[vendor_id]['items'].append(order_item)
            vendors_map[vendor_id]['subtotal'] += subtotal
        
        # Create order suborders (one per vendor) and reserve stock
        for vendor_id, vendor_data in vendors_map.items():
            vendor = vendor_data['vendor']
            subtotal = vendor_data['subtotal']
            
            # Create suborder
            OrderSuborder.objects.create(
                order=order,
                vendor=vendor,
                subtotal=subtotal,
                status='pending'
            )
            
            # Reserve stock and create inventory movements
            for order_item in vendor_data['items']:
                stock = order_item.product.stock_entries.filter(vendor=vendor).first()
                
                # Reserve stock
                stock.reserved_quantity += order_item.quantity
                stock.save()
                
                # Create inventory movement for audit trail
                InventoryMovement.objects.create(
                    stock=stock,
                    movement_type='sale',
                    quantity_change=-order_item.quantity,
                    previous_quantity=stock.quantity + order_item.quantity,
                    new_quantity=stock.quantity,
                    reference_id=order.id
                )
            
            # Credit vendor wallet (pending until order shipped)
            wallet, _ = VendorWallet.objects.get_or_create(vendor=vendor)
            wallet.pending_balance += subtotal
            wallet.save()
        
        return order
    
    @staticmethod
    @transaction.atomic
    def confirm_order(order, changed_by=None):
        """Confirm order and reduce stock."""
        if order.status != 'pending':
            raise ValueError('Only pending orders can be confirmed')
        
        for order_item in order.items.all():
            stock = order_item.product.stock_entries.filter(
                vendor=order_item.vendor
            ).first()
            
            if not stock:
                raise ValueError('Stock not found')
            
            # Reduce actual stock
            stock.quantity -= order_item.quantity
            stock.reserved_quantity -= order_item.quantity
            stock.save()
        
        old_status = order.status
        order.status = OrderStatus.CONFIRMED
        order.save()
        if changed_by:
            OrderService.record_status_change(order, old_status, order.status, changed_by, 'system', 'Order confirmed')
        return order
    
    @staticmethod
    @transaction.atomic
    def mark_order_shipped(order, tracking_number, delivery_fee=Decimal('0.00'), changed_by=None, changed_by_role='vendor'):
        """
        Mark order as shipped and move vendor pending balance to available.
        
        Args:
            order: Order instance
            tracking_number: Shipment tracking number
            delivery_fee: Delivery fee amount
        """
        if order.status not in [OrderStatus.PENDING, OrderStatus.PROCESSING, OrderStatus.CONFIRMED]:
            raise ValueError('Order cannot be shipped in current status')
        
        # Create shipment
        shipment = Shipment.objects.create(
            order=order,
            tracking_number=tracking_number,
            delivery_fee=delivery_fee,
            status='shipped'
        )

        old_status = order.status
        order.status = OrderStatus.SHIPPED
        order.tracking_number = tracking_number
        order.save()

        if changed_by:
            OrderService.record_status_change(order, old_status, order.status, changed_by, changed_by_role, 'Order shipped')
        
        # Move pending balance to available for all vendors
        for suborder in order.suborders.all():
            vendor = suborder.vendor
            wallet = vendor.vendor_wallet
            
            # Move pending to available
            wallet.available_balance += suborder.subtotal
            wallet.pending_balance -= suborder.subtotal
            wallet.save()

            old_suborder_status = suborder.status
            suborder.status = OrderStatus.SHIPPED
            suborder.save(update_fields=['status', 'updated_at'])
            if changed_by:
                OrderService.record_status_change(
                    order,
                    old_suborder_status,
                    suborder.status,
                    changed_by,
                    changed_by_role,
                    'Vendor shipped suborder',
                    suborder=suborder,
                )
        return order
    
    @staticmethod
    @transaction.atomic
    def mark_order_out_for_delivery(order, changed_by=None, notes=''):
        """Mark order as out for delivery."""
        if order.status != OrderStatus.SHIPPED:
            raise ValueError('Only shipped orders can be moved out for delivery')

        old_status = order.status
        order.status = OrderStatus.OUT_FOR_DELIVERY
        order.save(update_fields=['status', 'updated_at'])

        if hasattr(order, 'shipment'):
            order.shipment.status = 'in_transit'
            order.shipment.save(update_fields=['status', 'last_update_time'])

        if changed_by:
            OrderService.record_status_change(order, old_status, order.status, changed_by, 'admin', notes or 'Order is out for delivery')
        return order

    @staticmethod
    @transaction.atomic
    def mark_order_delivered(order, changed_by=None, notes=''):
        """Mark order as delivered."""
        if order.status not in [OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY]:
            raise ValueError('Only shipped or out-for-delivery orders can be delivered')
        
        if hasattr(order, 'shipment'):
            order.shipment.status = 'delivered'
            order.shipment.pickup_time = timezone.now()
            order.shipment.save(update_fields=['status', 'pickup_time', 'last_update_time'])
        
        old_status = order.status
        order.status = OrderStatus.DELIVERED
        order.delivered_at = timezone.now()
        order.save()

        if changed_by:
            OrderService.record_status_change(order, old_status, order.status, changed_by, 'buyer', notes or 'Buyer confirmed delivery')
        return order
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order, changed_by=None, reason=''):
        """
        Cancel order and reverse stock/wallet changes.
        
        Args:
            order: Order instance
            reason: Cancellation reason
        """
        if order.status in ['delivered', 'cancelled']:
            raise ValueError('Order cannot be cancelled in current status')
        
        # Reverse stock changes
        for order_item in order.items.all():
            stock = order_item.product.stock_entries.filter(
                vendor=order_item.vendor
            ).first()
            
            if stock:
                stock.quantity += order_item.quantity
                stock.reserved_quantity -= order_item.quantity
                stock.save()
                
                # Create reversal inventory movement
                InventoryMovement.objects.create(
                    stock=stock,
                    movement_type='cancellation',
                    quantity_change=order_item.quantity,
                    previous_quantity=stock.quantity - order_item.quantity,
                    new_quantity=stock.quantity,
                    reference_id=order.id
                )
        
        # Reverse vendor wallet changes (both pending and available)
        for suborder in order.suborders.all():
            wallet = suborder.vendor.vendor_wallet
            wallet.pending_balance -= suborder.subtotal
            wallet.available_balance -= suborder.subtotal
            wallet.save()
        
        old_status = order.status
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = timezone.now()
        order.cancellation_reason = reason
        order.save()

        if changed_by:
            OrderService.record_status_change(order, old_status, order.status, changed_by, 'buyer', reason or 'Order cancelled')
        return order

    @staticmethod
    def get_tracking_timeline(order):
        """Return serialized tracking history for an order."""
        history = order.status_history.select_related('changed_by', 'suborder').all()
        return list(history)

