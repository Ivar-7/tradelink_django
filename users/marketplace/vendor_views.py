from datetime import datetime, timezone

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers as s
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tradelink_django.supabase_client import SupabaseService
from users.models import UserRole
from users.permissions import IsAdminUser

from .shared import (
    STORE_PROFILES,
    USER_SETTINGS,
    USER_NOTIFICATIONS,
    VENDOR_APPLICATIONS,
    default_vendor_application,
)


# ─────────────────────────────────────────────
# Vendor Application Views
# ─────────────────────────────────────────────

class VendorApplyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Apply to become a vendor",
        request=inline_serializer(
            name="VendorApplyRequest",
            fields={
                "business_name": s.CharField(required=False, allow_blank=True),
                "business_email": s.EmailField(required=False),
                "business_phone": s.CharField(required=False, allow_blank=True),
                "tax_id": s.CharField(required=False, allow_blank=True),
                "review_notes": s.CharField(required=False, allow_blank=True),
            },
        ),
        responses=inline_serializer(
            name="VendorApplicationResponse",
            fields={
                "user_id": s.CharField(),
                "business_name": s.CharField(),
                "business_email": s.EmailField(),
                "business_phone": s.CharField(),
                "tax_id": s.CharField(),
                "status": s.CharField(),
                "submitted_at": s.CharField(allow_null=True),
                "reviewed_at": s.CharField(allow_null=True),
                "review_notes": s.CharField(allow_blank=True),
            },
        ),
    )
    def post(self, request):
        user_id = str(request.user.id)
        payload = default_vendor_application(user_id)
        payload.update(
            {
                "business_name": request.data.get("business_name", ""),
                "business_email": request.data.get("business_email", request.user.email),
                "business_phone": request.data.get("business_phone", ""),
                "tax_id": request.data.get("tax_id", ""),
                "status": "submitted",
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "review_notes": request.data.get("review_notes", ""),
            }
        )
        VENDOR_APPLICATIONS[user_id] = payload
        return Response(payload, status=status.HTTP_201_CREATED)


class VendorApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get vendor application for current user",
        responses=inline_serializer(
            name="VendorApplicationGetResponse",
            fields={
                "user_id": s.CharField(),
                "business_name": s.CharField(),
                "business_email": s.EmailField(),
                "business_phone": s.CharField(),
                "tax_id": s.CharField(),
                "status": s.CharField(),
                "submitted_at": s.CharField(allow_null=True),
                "reviewed_at": s.CharField(allow_null=True),
                "review_notes": s.CharField(allow_blank=True),
            },
        ),
    )
    def get(self, request):
        user_id = str(request.user.id)
        return Response(VENDOR_APPLICATIONS.get(user_id, default_vendor_application(user_id)))

    @extend_schema(
        summary="Update (patch) vendor application for current user",
        request=inline_serializer(
            name="VendorApplicationPatchRequest",
            fields={
                "business_name": s.CharField(required=False, allow_blank=True),
                "business_email": s.EmailField(required=False),
                "business_phone": s.CharField(required=False, allow_blank=True),
                "tax_id": s.CharField(required=False, allow_blank=True),
                "review_notes": s.CharField(required=False, allow_blank=True),
            },
        ),
        responses=OpenApiResponse(description="Updated application object"),
    )
    def patch(self, request):
        user_id = str(request.user.id)
        application = VENDOR_APPLICATIONS.get(user_id, default_vendor_application(user_id))
        updatable = {
            "business_name",
            "business_email",
            "business_phone",
            "tax_id",
            "review_notes",
        }
        for key, value in request.data.items():
            if key in updatable:
                application[key] = value
        VENDOR_APPLICATIONS[user_id] = application
        return Response(application)


class AdminVendorsView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="List vendor applications (admin)",
        parameters=[
            OpenApiParameter("status", description="Filter by application status", required=False, type=str)
        ],
        responses=OpenApiResponse(description="List of vendor applications"),
    )
    def get(self, request):
        status_filter = request.query_params.get("status")
        applications = list(VENDOR_APPLICATIONS.values())
        if status_filter:
            applications = [a for a in applications if a.get("status") == status_filter]
        return Response({"vendors": applications, "total": len(applications)})


class AdminVendorStatusView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Update vendor application status (admin)",
        request=inline_serializer(
            name="AdminVendorStatusRequest",
            fields={
                "status": s.ChoiceField(choices=["pending", "submitted", "approved", "rejected"]),
                "review_notes": s.CharField(required=False, allow_blank=True),
            },
        ),
        responses=OpenApiResponse(description="Updated application object or 404"),
    )
    def patch(self, request, user_id):
        application = VENDOR_APPLICATIONS.get(user_id)
        if not application:
            return Response({"detail": "Vendor application not found."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status")
        if new_status not in {"pending", "submitted", "approved", "rejected"}:
            return Response(
                {"detail": "status must be one of pending, submitted, approved, rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application["status"] = new_status
        application["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        application["review_notes"] = request.data.get("review_notes", application.get("review_notes", ""))
        VENDOR_APPLICATIONS[user_id] = application

        if new_status == "approved":
            from users.models import User

            user = User.objects.filter(id=user_id).first()
            if user:
                user.role = UserRole.VENDOR
                user.save(update_fields=["role"])

            # Create vendor_profile in Supabase if it doesn't exist
            existing = (
                SupabaseService.get_client()
                .table("vendor_profile")
                .select("vendor_id")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            if not existing.data:
                SupabaseService.get_client().table("vendor_profile").insert({
                    "user_id": user_id,
                    "is_verified": True,
                    "vendor_type": "individual",
                }).execute()

        return Response(application)


class VendorProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve vendor profile for current user",
        responses=inline_serializer(
            name="VendorProfileResponse",
            fields={
                "id": s.CharField(),
                "email": s.EmailField(),
                "username": s.CharField(),
                "first_name": s.CharField(),
                "last_name": s.CharField(),
                "phone_number": s.CharField(),
                "role": s.CharField(),
            },
        ),
    )
    def get(self, request):
        user = request.user
        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number,
                "role": user.role,
            }
        )

    @extend_schema(
        summary="Update vendor profile fields for current user",
        request=inline_serializer(
            name="VendorProfilePatchRequest",
            fields={
                "first_name": s.CharField(required=False, allow_blank=True),
                "last_name": s.CharField(required=False, allow_blank=True),
                "phone_number": s.CharField(required=False, allow_blank=True),
                "username": s.CharField(required=False),
            },
        ),
        responses=OpenApiResponse(description="Updated profile object"),
    )
    def patch(self, request):
        user = request.user
        updatable = ["first_name", "last_name", "phone_number", "username"]
        changed = []
        for field in updatable:
            if field in request.data:
                setattr(user, field, request.data.get(field))
                changed.append(field)
        if changed:
            user.save(update_fields=changed)
        return self.get(request)


# ─────────────────────────────────────────────
# Store & Settings Views
# ─────────────────────────────────────────────

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
        try:
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
        except KeyError:
            return Response(
                {"detail": "Vendor profile not found. Apply and get approved first."},
                status=status.HTTP_404_NOT_FOUND,
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
        try:
            store = STORE_PROFILES.get(user_id, {})
        except KeyError:
            return Response(
                {"detail": "Vendor profile not found. Apply and get approved first."},
                status=status.HTTP_404_NOT_FOUND,
            )

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


# ─────────────────────────────────────────────
# Placeholder views for other marketplace endpoints
# (Keep your existing implementations or fill in as needed)
# ─────────────────────────────────────────────

class NotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = str(request.user.id)
        notifications = USER_NOTIFICATIONS.get(user_id, {"notifications": [], "unread_count": 0})
        return Response(notifications)


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        user_id = str(request.user.id)
        data = USER_NOTIFICATIONS.get(user_id, {})
        notifications = data.get("notifications", [])
        for n in notifications:
            if n.get("id") == notification_id:
                n["read"] = True
        USER_NOTIFICATIONS[user_id] = data
        return Response({"detail": "Marked as read."})


class PayoutsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"payouts": []})


class PayoutDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, payout_id):
        return Response({"payout_id": payout_id})


class WalletView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"balance": 0, "currency": "KES"})


class RevenueReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"revenue": 0})


class OrdersReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"orders": 0})


class ProductsReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"products": 0})


class CustomReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"report": []})


class ExportReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"detail": "Export not implemented."})


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "total_sales": 0,
            "total_orders": 0,
            "total_products": 0,
            "pending_payouts": 0,
        })