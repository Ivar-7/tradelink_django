from rest_framework import serializers

class SalesFilterSerializer(serializers.Serializer):
    range = serializers.ChoiceField(choices=['today','7d','30d','90d'], default='30d')
    status = serializers.ChoiceField(choices=['all','pending','processing','delivered','cancelled'], default='all')
    granularity = serializers.ChoiceField(choices=['hourly','daily','weekly','monthly'], default='daily')

class OrdersFilterSerializer(serializers.Serializer):
    range = serializers.ChoiceField(choices=['today','7d','30d','90d'], default='30d')
    status = serializers.ChoiceField(choices=['all','pending','processing','shipped','delivered','cancelled'], default='all')
    shipping_type = serializers.ChoiceField(choices=['all','home','pickup'], default='all')
    sort = serializers.ChoiceField(choices=['date','amount_desc','status'], default='date')
    search = serializers.CharField(required=False, allow_blank=True)

class ProductsFilterSerializer(serializers.Serializer):
    range = serializers.ChoiceField(choices=['7d','30d','90d','all'], default='30d')
    sort = serializers.ChoiceField(choices=['qty_desc','qty_asc','revenue_desc'], default='qty_desc')
    search = serializers.CharField(required=False, allow_blank=True)
