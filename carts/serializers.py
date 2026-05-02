from rest_framework import serializers

from products.services import ProductService


class CartItemCreateUpdateSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        if not ProductService.resolve_stock_id(value):
            raise serializers.ValidationError("Product stock not found.")
        return value
