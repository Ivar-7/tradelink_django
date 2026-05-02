from datetime import datetime, timezone

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers as s
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .shared import USER_NOTIFICATIONS


class NotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List notifications for current user",
        responses=inline_serializer(
            name="NotificationsListResponse",
            fields={
                "notifications": s.ListField(child=s.DictField()),
                "total": s.IntegerField(),
            },
        ),
    )
    def get(self, request):
        user_id = str(request.user.id)
        notifications = USER_NOTIFICATIONS.get(user_id, [])
        return Response({"notifications": notifications, "total": len(notifications)})


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark a notification as read",
        parameters=[
            OpenApiParameter("notification_id", description="ID of notification to mark read", required=True, type=str)
        ],
        responses=OpenApiResponse(description="Updated notification object or 404"),
    )
    def patch(self, request, notification_id):
        user_id = str(request.user.id)
        notifications = USER_NOTIFICATIONS.get(user_id, [])
        for item in notifications:
            if str(item.get("id")) == str(notification_id):
                item["read"] = True
                item["read_at"] = datetime.now(timezone.utc).isoformat()
                return Response(item)
        return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
