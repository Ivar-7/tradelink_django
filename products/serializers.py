from rest_framework import serializers


class ProductCreateUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    price = serializers.FloatField(min_value=0)
    description = serializers.CharField(required=False, allow_blank=True)
    stock_quantity = serializers.IntegerField(required=False, min_value=0)
    image_url = serializers.URLField(required=False, allow_blank=True)
    category_id = serializers.UUIDField(required=False, allow_null=True)
