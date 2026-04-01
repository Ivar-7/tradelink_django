from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items with product details."""
    product_id = serializers.CharField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['product_id', 'product_name', 'product_image', 'quantity', 'unit_price', 'subtotal']
        read_only_fields = ['product_id', 'product_name', 'product_image', 'subtotal']

    def get_product_image(self, obj):
        return obj.product.image_url or ''


class CartItemCreateUpdateSerializer(serializers.Serializer):
    """Serializer for adding/updating cart items."""
    product_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        try:
            Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found.")
        return value


class CartSerializer(serializers.ModelSerializer):
    """Serializer for cart with items."""
    products = CartItemSerializer(source='items', many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user_id', 'date_created', 'total_price', 'products']
        read_only_fields = ['id', 'user_id', 'date_created', 'total_price', 'products']
