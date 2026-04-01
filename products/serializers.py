from rest_framework import serializers
from .models import Product
from product_categories.serializers import ProductCategorySerializer


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
            'name', 'price', 'description', 'stock_quantity', 'image_url', 'category'
        ]

