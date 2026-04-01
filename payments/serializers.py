from rest_framework import serializers
from .models import Payment, PaymentStatus
from decimal import Decimal


class PaymentMethodSerializer(serializers.Serializer):
    """Serializer for payment method."""
    id = serializers.CharField()
    brand = serializers.CharField()
    last4 = serializers.CharField()
    expiry_month = serializers.CharField()
    expiry_year = serializers.CharField()
    holder_name = serializers.CharField()
    is_default = serializers.BooleanField()


class PaymentMethodCreateSerializer(serializers.Serializer):
    """Serializer for creating payment method."""
    brand = serializers.CharField()
    card_number = serializers.CharField()
    expiry_month = serializers.CharField()
    expiry_year = serializers.CharField()
    holder_name = serializers.CharField()

    def validate_card_number(self, value):
        # Remove spaces and validate length
        clean_number = value.replace(' ', '')
        if not clean_number.isdigit() or len(clean_number) < 13:
            raise serializers.ValidationError("Invalid card number.")
        return value


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payment."""
    user_id = serializers.CharField(source='user.id', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'user_id', 'order_id', 'amount', 'payment_provider',
            'status', 'created_at', 'phone_number', 'payment_method_id'
        ]
        read_only_fields = ['id', 'user_id', 'created_at']


class PaymentCreateSerializer(serializers.Serializer):
    """Serializer for creating payment."""
    order_id = serializers.CharField()
    payment_provider = serializers.ChoiceField(choices=['mpesa', 'card', 'bank_transfer'])
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    payment_method_id = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        provider = attrs.get('payment_provider')
        if provider == 'card' and not attrs.get('payment_method_id'):
            raise serializers.ValidationError(
                {'payment_method_id': 'Required for card payments'}
            )
        if provider == 'mpesa' and not attrs.get('phone_number'):
            raise serializers.ValidationError(
                {'phone_number': 'Required for M-Pesa payments'}
            )
        return attrs
