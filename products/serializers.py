from rest_framework import serializers
from .models import Product
from product_categories.serializers import ProductCategorySerializer
from .models import Stock, InventoryMovement


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for product with all details."""
    category_id = serializers.CharField(source='category.id', read_only=True)
    category = ProductCategorySerializer(read_only=True)
    vendor_id = serializers.CharField(source='vendor.id', read_only=True)
    vendor_name = serializers.CharField(source='vendor.username', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'description', 'stock_quantity', 'image_url',
            'category_id', 'category', 'vendor_id', 'vendor_name',
            'average_rating', 'review_count', 'created_at'
        ]
        read_only_fields = [
            'id', 'category_id', 'category', 'vendor_id', 'vendor_name',
            'average_rating', 'review_count', 'created_at'
        ]


class ProductListSerializer(serializers.ModelSerializer):
    """Minimal serializer for product lists."""
    category_id = serializers.CharField(source='category.id', read_only=True)
    vendor_id = serializers.CharField(source='vendor.id', read_only=True)
    vendor_name = serializers.CharField(source='vendor.username', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'description', 'stock_quantity', 'image_url',
            'category_id', 'vendor_id', 'vendor_name', 'average_rating',
            'review_count', 'created_at'
        ]
        read_only_fields = fields


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products."""
    class Meta:
        model = Product
        fields = [

            'name', 'price', 'description', 'stock_quantity', 'image_url', 'category', 'is_active'
        ]


class StockSerializer(serializers.ModelSerializer):
    """Serializer for product stock."""
    product_id = serializers.CharField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    vendor_id = serializers.CharField(source='vendor.id', read_only=True)
    vendor_name = serializers.CharField(source='vendor.username', read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)
    discounted_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Stock
        fields = [
            'id', 'product_id', 'product_name', 'vendor_id', 'vendor_name',
            'quantity', 'available_quantity', 'reserved_quantity', 'price',
            'discounted_price', 'is_flash_sale', 'discount_percentage', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'available_quantity']


class InventoryMovementSerializer(serializers.ModelSerializer):
    """Serializer for inventory movement audit trail."""
    stock_id = serializers.CharField(source='stock.id', read_only=True)
    product_id = serializers.CharField(source='stock.product.id', read_only=True)
    product_name = serializers.CharField(source='stock.product.name', read_only=True)
    
    class Meta:
        model = InventoryMovement
        fields = [
            'id', 'stock_id', 'product_id', 'product_name', 'movement_type',
            'quantity_change', 'previous_quantity', 'new_quantity',
            'reference_id', 'created_at'
        ]
        read_only_fields = fields

