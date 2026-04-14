from rest_framework import serializers
from .models import ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    """Serializer for product category."""
    parent_id = serializers.CharField(source='parent.id', read_only=True)

    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description', 'image_url', 'parent', 'parent_id', 'sort_order']
        read_only_fields = ['id']
