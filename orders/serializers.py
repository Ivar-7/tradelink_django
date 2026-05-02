from rest_framework import serializers


class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)


class DeliveryAddressCreateSerializer(serializers.Serializer):
    county = serializers.CharField()
    city = serializers.CharField()
    postal_address = serializers.CharField()
    user_contact = serializers.CharField()


class OrderCreateSerializer(serializers.Serializer):
    shipping_method = serializers.ChoiceField(choices=[("pickup", "pickup"), ("delivery", "delivery")])
    products = OrderItemCreateSerializer(many=True, required=False)
    delivery_address = DeliveryAddressCreateSerializer(required=False)


class OrderCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)


class OrderIssueCreateSerializer(serializers.Serializer):
    type = serializers.CharField()
    details = serializers.CharField()


class ReturnRequestCreateSerializer(serializers.Serializer):
    reason = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True)
