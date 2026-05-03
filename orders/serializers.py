from rest_framework import serializers


# ---------------------------
# ORDER ITEM
# ---------------------------

class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()   # ✅ enforce real UUID (not random string)
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        # future-safe: prevent weird values
        if data["quantity"] <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return data


# ---------------------------
# DELIVERY ADDRESS
# ---------------------------

class DeliveryAddressCreateSerializer(serializers.Serializer):
    county = serializers.CharField(max_length=100)
    city = serializers.CharField(max_length=100)
    postal_address = serializers.CharField(max_length=20)
    user_contact = serializers.CharField(max_length=20)

    def validate_user_contact(self, value):
        # basic sanity check (you can improve later)
        if not value.startswith("+"):
            raise serializers.ValidationError("Phone must start with '+' and country code.")
        return value


# ---------------------------
# ORDER CREATE
# ---------------------------

class OrderCreateSerializer(serializers.Serializer):
    SHIPPING_CHOICES = (
        ("pickup", "pickup"),
        ("delivery", "delivery"),
    )

    shipping_method = serializers.ChoiceField(choices=SHIPPING_CHOICES)
    products = OrderItemCreateSerializer(many=True, required=False)
    delivery_address = DeliveryAddressCreateSerializer(required=False)

    def validate(self, data):
        shipping = data.get("shipping_method")
        products = data.get("products")

        # ❌ No items at all
        if not products:
            raise serializers.ValidationError("At least one product is required.")

        # ❌ Delivery requires address
        if shipping == "delivery" and not data.get("delivery_address"):
            raise serializers.ValidationError(
                "Delivery address is required when shipping_method is 'delivery'."
            )

        return data


# ---------------------------
# ORDER CANCEL
# ---------------------------

class OrderCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255)

    def validate_reason(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Cancellation reason is too short.")
        return value


# ---------------------------
# ORDER ISSUE
# ---------------------------

class OrderIssueCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=[
            ("damaged", "damaged"),
            ("missing_item", "missing_item"),
            ("wrong_item", "wrong_item"),
            ("other", "other"),
        ]
    )
    details = serializers.CharField(max_length=500)


# ---------------------------
# RETURN REQUEST
# ---------------------------

class ReturnRequestCreateSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_reason(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Return reason is too short.")
        return value