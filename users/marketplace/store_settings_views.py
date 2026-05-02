from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers as s
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .shared import STORE_PROFILES, USER_SETTINGS


class StoreView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get store profile for current vendor",
        responses=inline_serializer(
            name="StoreProfileResponse",
            fields={
                "store_name": s.CharField(),
                "description": s.CharField(),
                "logo_url": s.CharField(),
                "banner_url": s.CharField(),
                "support_email": s.EmailField(),
                "support_phone": s.CharField(),
            },
        ),
    )
    def get(self, request):
        user_id = str(request.user.id)
        store = STORE_PROFILES.get(
            user_id,
            {
                "store_name": request.user.username,
                "description": "",
                "logo_url": "",
                "banner_url": "",
                "support_email": request.user.email,
                "support_phone": request.user.phone_number,
            },
        )
        return Response(store)

    @extend_schema(
        summary="Update store profile for current vendor",
        request=inline_serializer(
            name="StoreProfilePatchRequest",
            fields={
                "store_name": s.CharField(required=False),
                "description": s.CharField(required=False, allow_blank=True),
                "logo_url": s.CharField(required=False, allow_blank=True),
                "banner_url": s.CharField(required=False, allow_blank=True),
                "support_email": s.EmailField(required=False),
                "support_phone": s.CharField(required=False, allow_blank=True),
            },
        ),
        responses=OpenApiResponse(description="Updated store object"),
    )
    def patch(self, request):
        user_id = str(request.user.id)
        store = STORE_PROFILES.get(user_id, {})
        updatable = {
            "store_name",
            "description",
            "logo_url",
            "banner_url",
            "support_email",
            "support_phone",
        }
        for key, value in request.data.items():
            if key in updatable:
                store[key] = value
        STORE_PROFILES[user_id] = store
        return Response(store)


class SettingsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get vendor settings",
        responses=inline_serializer(
            name="VendorSettingsResponse",
            fields={
                "currency": s.CharField(),
                "timezone": s.CharField(),
                "email_notifications": s.BooleanField(),
                "order_auto_confirm": s.BooleanField(),
            },
        ),
    )
    def get(self, request):
        user_id = str(request.user.id)
        default = {
            "currency": "KES",
            "timezone": "UTC",
            "email_notifications": True,
            "order_auto_confirm": False,
        }
        return Response(USER_SETTINGS.get(user_id, default))

    @extend_schema(
        summary="Update vendor settings",
        request=inline_serializer(
            name="VendorSettingsPatchRequest",
            fields={
                "currency": s.CharField(required=False),
                "timezone": s.CharField(required=False),
                "email_notifications": s.BooleanField(required=False),
                "order_auto_confirm": s.BooleanField(required=False),
            },
        ),
        responses=OpenApiResponse(description="Updated settings"),
    )
    def patch(self, request):
        user_id = str(request.user.id)
        settings_data = USER_SETTINGS.get(user_id, {})
        settings_data.update(request.data)
        USER_SETTINGS[user_id] = settings_data
        return Response(settings_data)
