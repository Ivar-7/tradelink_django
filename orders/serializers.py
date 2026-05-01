from rest_framework import serializers
from django.utils import timezone
from .models import (
    Order, OrderItem, OrderSuborder, Shipment, OrderStatusHistory, DeliveryAddress, OrderIssueReport, ReturnRequest,
    OrderStatus, ShippingMethod
)


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    product_id = serializers.CharField(source='product.id', read_only=True)
    vendor_id = serializers.CharField(source='vendor.id', read_only=True)
    vendor_name = serializers.CharField(source='vendor.username', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['product_id', 'product_name', 'product_image', 'quantity', 'unit_price', 'subtotal', 'vendor_id', 'vendor_name']
        read_only_fields = fields
class OrderSuborderSerializer(serializers.ModelSerializer):
    """Serializer for order suborder (per vendor)."""
    vendor_id = serializers.CharField(source='vendor.id', read_only=True)
    vendor_name = serializers.CharField(source='vendor.username', read_only=True)
    
    class Meta:
        model = OrderSuborder
        fields = ['id', 'vendor_id', 'vendor_name', 'subtotal', 'status', 'created_at']
        read_only_fields = fields


class ShipmentSerializer(serializers.ModelSerializer):
    """Serializer for shipment tracking."""
    class Meta:
        model = Shipment
        fields = ['id', 'tracking_number', 'status', 'delivery_fee', 'pickup_time', 'created_at', 'last_update_time']
        read_only_fields = fields


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for order status history entries."""
    changed_by_email = serializers.CharField(source='changed_by.email', read_only=True)
    suborder_id = serializers.CharField(source='suborder.id', read_only=True, allow_null=True)

    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'order', 'suborder_id', 'old_status', 'new_status',
            'changed_by_email', 'changed_by_role', 'notes', 'location', 'created_at'
        ]
        read_only_fields = fields




class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items in checkout."""
    product_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)


class DeliveryAddressSerializer(serializers.ModelSerializer):
    """Serializer for delivery address."""
    class Meta:
        model = DeliveryAddress
        fields = ['county', 'city', 'postal_address', 'user_contact']


class DeliveryAddressCreateSerializer(serializers.Serializer):
    """Serializer for creating delivery address in checkout."""
    county = serializers.CharField()
    city = serializers.CharField()
    postal_address = serializers.CharField()
    user_contact = serializers.CharField()


class OrderIssueReportSerializer(serializers.ModelSerializer):
    """Serializer for order issue reports."""
    class Meta:
        model = OrderIssueReport
        fields = ['type', 'details', 'reported_at']
        read_only_fields = ['reported_at']


class ReturnRequestTimelineSerializer(serializers.Serializer):
    """Timeline for a return request."""
    requested_at = serializers.DateTimeField(allow_null=True)
    approved_at = serializers.DateTimeField(allow_null=True)
    shipped_back_at = serializers.DateTimeField(allow_null=True)
    refunded_at = serializers.DateTimeField(allow_null=True)


class ReturnRequestSerializer(serializers.ModelSerializer):
    """Serializer for return requests."""
    timeline = ReturnRequestTimelineSerializer(read_only=True)

    class Meta:
        model = ReturnRequest
        fields = ['id', 'created_at', 'status', 'reason', 'notes', 'timeline']
        read_only_fields = ['id', 'created_at', 'status', 'timeline']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for full order detail."""
    user_id = serializers.CharField(source='user.id', read_only=True)
    products = OrderItemSerializer(source='items', many=True, read_only=True)
    delivery_address = DeliveryAddressSerializer(read_only=True)
    issue_report = OrderIssueReportSerializer(read_only=True)
    return_request = ReturnRequestSerializer(read_only=True)
    suborders = OrderSuborderSerializer(many=True, read_only=True)
    shipment = ShipmentSerializer(read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user_id', 'order_date', 'order_amount', 'products', 'suborders', 'status',
            'shipping_method', 'tracking_number', 'shipment', 'delivered_at', 'cancelled_at',
            'cancellation_reason', 'issue_report', 'return_request', 'delivery_address',
            'status_history'
        ]
        read_only_fields = ['id', 'user_id', 'order_date', 'order_amount']


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating an order during checkout."""
    shipping_method = serializers.ChoiceField(choices=ShippingMethod.choices)
    products = OrderItemCreateSerializer(many=True, required=False)
    delivery_address = DeliveryAddressCreateSerializer(required=False)

    def validate_shipping_method(self, value):
        if value not in dict(ShippingMethod.choices):
            raise serializers.ValidationError(f"Invalid shipping method: {value}")
        return value


class OrderCancelSerializer(serializers.Serializer):
    """Serializer for cancelling an order."""
    reason = serializers.CharField(required=True)


class OrderIssueCreateSerializer(serializers.Serializer):
    """Serializer for reporting an order issue."""
    type = serializers.CharField()
    details = serializers.CharField()


class ReturnRequestCreateSerializer(serializers.Serializer):
    """Serializer for creating a return request."""
    reason = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True)


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for order list response."""
    user_id = serializers.CharField(source='user.id', read_only=True)
    products = OrderItemSerializer(source='items', many=True, read_only=True)
    shipment = ShipmentSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user_id', 'order_date', 'order_amount', 'products', 'status',
            'shipping_method', 'tracking_number', 'shipment'
        ]
        read_only_fields = fields
