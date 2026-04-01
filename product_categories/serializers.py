from rest_framework import serializers
from .models import ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    """Serializer for product category."""
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description', 'image_url']
        read_only_fields = ['id']
