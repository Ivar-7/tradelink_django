from rest_framework import serializers


# ---------------------------
# PRODUCT SERIALIZERS
# ---------------------------

class ProductCreateUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    price = serializers.FloatField(min_value=0)
    description = serializers.CharField(required=False, allow_blank=True)
    stock_quantity = serializers.IntegerField(required=False, min_value=0)
    image_url = serializers.URLField(required=False, allow_blank=True)
    category_id = serializers.UUIDField(required=False, allow_null=True)


class ProductListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    price = serializers.FloatField()
    image_url = serializers.URLField(allow_null=True, required=False)


class ProductSerializer(serializers.Serializer):  # detail view
    id = serializers.UUIDField()
    name = serializers.CharField()
    price = serializers.FloatField()
    description = serializers.CharField()
    stock_quantity = serializers.IntegerField()
    image_url = serializers.URLField(allow_null=True, required=False)
    category_id = serializers.UUIDField(allow_null=True, required=False)


# ---------------------------
# STOCK SERIALIZER
# ---------------------------

class StockSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    product_id = serializers.UUIDField()
    vendor_id = serializers.UUIDField()
    quantity = serializers.IntegerField()
    price = serializers.FloatField()


# ---------------------------
# INVENTORY MOVEMENT SERIALIZER
# ---------------------------

class InventoryMovementSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    stock_id = serializers.UUIDField()
    change = serializers.IntegerField()
    movement_type = serializers.CharField()
    created_at = serializers.DateTimeField()



class ProductDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField()    
    name = serializers.CharField()
    price = serializers.FloatField()
    description = serializers.CharField()
    stock_quantity = serializers.IntegerField()
    image_url = serializers.URLField(allow_null=True, required=False)
    category_id = serializers.UUIDField(allow_null=True, required=False)