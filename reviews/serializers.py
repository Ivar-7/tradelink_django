from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for product reviews."""
    user_id = serializers.CharField(source='user.id', read_only=True)
    username = serializers.CharField(read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'user_id', 'username', 'product_id', 'rating_value',
            'comment', 'verified_purchase', 'helpful_count', 'date'
        ]
        read_only_fields = ['id', 'user_id', 'username', 'helpful_count', 'date']


class ReviewCreateSerializer(serializers.Serializer):
    """Serializer for creating reviews."""
    rating_value = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=500, required=False, allow_blank=True)


class ReviewListSerializer(serializers.Serializer):
    """Serializer for review list response."""
    reviews = ReviewSerializer(many=True)
    total = serializers.IntegerField()
    average_rating = serializers.FloatField()
