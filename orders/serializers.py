from rest_framework import serializers
from django.utils import timezone
from .models import (
    Order, OrderItem, DeliveryAddress, OrderIssueReport, ReturnRequest,
    OrderStatus, ShippingMethod
)


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    product_id = serializers.CharField(source='product.id', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['product_id', 'product_name', 'product_image', 'quantity', 'unit_price', 'subtotal']
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

    class Meta:
        model = Order
        fields = [
            'id', 'user_id', 'order_date', 'order_amount', 'products', 'status',
            'shipping_method', 'tracking_number', 'delivered_at', 'cancelled_at',
            'cancellation_reason', 'issue_report', 'return_request', 'delivery_address'
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

    class Meta:
        model = Order
        fields = [
            'id', 'user_id', 'order_date', 'order_amount', 'products', 'status',
            'shipping_method', 'tracking_number'
        ]
        read_only_fields = fields
