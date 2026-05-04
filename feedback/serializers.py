from rest_framework import serializers
from .models import Feedback, FeedbackType


class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for feedback."""

    user_id = serializers.CharField(source="user.id", read_only=True)


class Meta:
    model = Feedback
    fields = ["id", "user_id", "type", "message", "created_at"]
    read_only_fields = ["id", "user_id", "created_at"]


class FeedbackCreateSerializer(serializers.Serializer):
    """Serializer for creating feedback."""

    type = serializers.ChoiceField(choices=FeedbackType.choices)
    message = serializers.CharField(min_length=10, max_length=1000)
