from datetime import datetime, timezone
from decimal import Decimal

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse, OpenApiParameter
from rest_framework import serializers as s

from orders.services import OrderService
from payments.services import PaymentService
from products.services import ProductService
from users.models import UserRole
from users.permissions import IsAdminUser


VENDOR_APPLICATIONS = {}
STORE_PROFILES = {}
USER_SETTINGS = {}
USER_NOTIFICATIONS = {}


def _default_vendor_application(user_id: str):
    return {
        "user_id": user_id,
        "business_name": "",
        "business_email": "",
        "business_phone": "",
        "tax_id": "",
        "status": "draft",
        "submitted_at": None,
        "reviewed_at": None,
        "review_notes": "",
    }


def _parse_iso(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


class VendorApplyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Apply to become a vendor',
        request=inline_serializer(
            name='VendorApplyRequest',
            fields={
                'business_name': s.CharField(required=False, allow_blank=True),
                'business_email': s.EmailField(required=False),
                'business_phone': s.CharField(required=False, allow_blank=True),
                'tax_id': s.CharField(required=False, allow_blank=True),
                'review_notes': s.CharField(required=False, allow_blank=True),
            }
        ),
        responses=inline_serializer(
            name='VendorApplicationResponse',
            fields={
                'user_id': s.CharField(),
                'business_name': s.CharField(),
                'business_email': s.EmailField(),
                'business_phone': s.CharField(),
                'tax_id': s.CharField(),
                'status': s.CharField(),
                'submitted_at': s.CharField(allow_null=True),
                'reviewed_at': s.CharField(allow_null=True),
                'review_notes': s.CharField(allow_blank=True),
            }
        ),
    )
    def post(self, request):
        user_id = str(request.user.id)
        payload = _default_vendor_application(user_id)
        payload.update({
            "business_name": request.data.get("business_name", ""),
            "business_email": request.data.get("business_email", request.user.email),
            "business_phone": request.data.get("business_phone", ""),
            "tax_id": request.data.get("tax_id", ""),
            "status": "submitted",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "review_notes": request.data.get("review_notes", ""),
        })
        VENDOR_APPLICATIONS[user_id] = payload
        return Response(payload, status=status.HTTP_201_CREATED)


class VendorApplicationView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary='Get vendor application for current user',
        responses=inline_serializer(
            name='VendorApplicationGetResponse',
            fields={
                'user_id': s.CharField(),
                'business_name': s.CharField(),
                'business_email': s.EmailField(),
                'business_phone': s.CharField(),
                'tax_id': s.CharField(),
                'status': s.CharField(),
                'submitted_at': s.CharField(allow_null=True),
                'reviewed_at': s.CharField(allow_null=True),
                'review_notes': s.CharField(allow_blank=True),
            },
        ),
    )
    def get(self, request):
        user_id = str(request.user.id)
        return Response(VENDOR_APPLICATIONS.get(user_id, _default_vendor_application(user_id)))
    @extend_schema(
        summary='Update (patch) vendor application for current user',
        request=inline_serializer(
            name='VendorApplicationPatchRequest',
            fields={
                'business_name': s.CharField(required=False, allow_blank=True),
                'business_email': s.EmailField(required=False),
                'business_phone': s.CharField(required=False, allow_blank=True),
                'tax_id': s.CharField(required=False, allow_blank=True),
                'review_notes': s.CharField(required=False, allow_blank=True),
            }
        ),
        responses=OpenApiResponse(description='Updated application object'),
    )
    def patch(self, request):
        user_id = str(request.user.id)
        application = VENDOR_APPLICATIONS.get(user_id, _default_vendor_application(user_id))
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
        summary='List vendor applications (admin)',
        parameters=[
            OpenApiParameter('status', description='Filter by application status', required=False, type=str),
        ],
        responses=OpenApiResponse(description='List of vendor applications'),
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
        summary='Update vendor application status (admin)',
        request=inline_serializer(
            name='AdminVendorStatusRequest',
            fields={
                'status': s.ChoiceField(choices=['pending', 'submitted', 'approved', 'rejected']),
                'review_notes': s.CharField(required=False, allow_blank=True),
            }
        ),
        responses=OpenApiResponse(description='Updated application object or 404'),
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

        return Response(application)


class VendorProfileView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary='Retrieve vendor profile for current user',
        responses=inline_serializer(
            name='VendorProfileResponse',
            fields={
                'id': s.CharField(),
                'email': s.EmailField(),
                'username': s.CharField(),
                'first_name': s.CharField(),
                'last_name': s.CharField(),
                'phone_number': s.CharField(),
                'role': s.CharField(),
            }
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
        summary='Update vendor profile fields for current user',
        request=inline_serializer(
            name='VendorProfilePatchRequest',
            fields={
                'first_name': s.CharField(required=False, allow_blank=True),
                'last_name': s.CharField(required=False, allow_blank=True),
                'phone_number': s.CharField(required=False, allow_blank=True),
                'username': s.CharField(required=False),
            }
        ),
        responses=OpenApiResponse(description='Updated profile object'),
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


class StoreView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary='Get store profile for current vendor',
        responses=inline_serializer(
            name='StoreProfileResponse',
            fields={
                'store_name': s.CharField(),
                'description': s.CharField(),
                'logo_url': s.CharField(),
                'banner_url': s.CharField(),
                'support_email': s.EmailField(),
                'support_phone': s.CharField(),
            }
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
        summary='Update store profile for current vendor',
        request=inline_serializer(
            name='StoreProfilePatchRequest',
            fields={
                'store_name': s.CharField(required=False),
                'description': s.CharField(required=False, allow_blank=True),
                'logo_url': s.CharField(required=False, allow_blank=True),
                'banner_url': s.CharField(required=False, allow_blank=True),
                'support_email': s.EmailField(required=False),
                'support_phone': s.CharField(required=False, allow_blank=True),
            }
        ),
        responses=OpenApiResponse(description='Updated store object'),
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
        summary='Get vendor settings',
        responses=inline_serializer(
            name='VendorSettingsResponse',
            fields={
                'currency': s.CharField(),
                'timezone': s.CharField(),
                'email_notifications': s.BooleanField(),
                'order_auto_confirm': s.BooleanField(),
            }
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
        summary='Update vendor settings',
        request=inline_serializer(
            name='VendorSettingsPatchRequest',
            fields={
                'currency': s.CharField(required=False),
                'timezone': s.CharField(required=False),
                'email_notifications': s.BooleanField(required=False),
                'order_auto_confirm': s.BooleanField(required=False),
            }
        ),
        responses=OpenApiResponse(description='Updated settings'),
    )
    def patch(self, request):
        user_id = str(request.user.id)
        settings_data = USER_SETTINGS.get(user_id, {})
        settings_data.update(request.data)
        USER_SETTINGS[user_id] = settings_data
        return Response(settings_data)


class NotificationsView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary='List notifications for current user',
        responses=inline_serializer(
            name='NotificationsListResponse',
            fields={
                'notifications': s.ListField(child=s.DictField()),
                'total': s.IntegerField(),
            }
        ),
    )
    def get(self, request):
        user_id = str(request.user.id)
        notifications = USER_NOTIFICATIONS.get(user_id, [])
        return Response({"notifications": notifications, "total": len(notifications)})


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary='Mark a notification as read',
        parameters=[
            OpenApiParameter('notification_id', description='ID of notification to mark read', required=True, type=str)
        ],
        responses=OpenApiResponse(description='Updated notification object or 404'),
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


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary='Vendor dashboard summary (orders, revenue, top products)',
        responses=inline_serializer(
            name='DashboardSummaryResponse',
            fields={
                'revenueToday': s.FloatField(),
                'ordersToday': s.IntegerField(),
                'pendingOrders': s.IntegerField(),
                'lowStockCount': s.IntegerField(),
                'topProducts': s.ListField(child=s.DictField()),
                'recentOrders': s.ListField(child=s.DictField()),
            }
        ),
    )
    def get(self, request):
        user_id = str(request.user.id)
        orders = OrderService.list_orders(user_id=user_id, is_admin=request.user.is_staff)
        products = ProductService.get_products({})

        now = datetime.now(timezone.utc)
        orders_today = 0
        revenue_today = Decimal("0")
        pending_orders = 0
        recent_orders = []

        for order in orders:
            status_value = str(order.get("status") or "").lower()
            if status_value in {"new", "pending", "confirmed"}:
                pending_orders += 1

            order_date = _parse_iso(order.get("order_date"))
            amount = Decimal(str(order.get("total_amount") or 0))
            if order_date and order_date.date() == now.date():
                orders_today += 1
                revenue_today += amount

            recent_orders.append(
                {
                    "id": order.get("order_id"),
                    "status": order.get("status"),
                    "total": float(amount),
                    "order_date": order.get("order_date"),
                }
            )

        low_stock_products = [p for p in products if int(p.get("stock") or 0) <= 5]
        top_products = sorted(
            products,
            key=lambda p: float(p.get("price") or 0) * int(p.get("stock") or 0),
            reverse=True,
        )[:5]

        return Response(
            {
                "revenueToday": float(revenue_today),
                "ordersToday": orders_today,
                "pendingOrders": pending_orders,
                "lowStockCount": len(low_stock_products),
                "topProducts": [
                    {
                        "id": p.get("product_id"),
                        "name": p.get("product_name"),
                        "price": float(p.get("price") or 0),
                        "stock": int(p.get("stock") or 0),
                    }
                    for p in top_products
                ],
                "recentOrders": recent_orders[:10],
            }
        )


class PayoutsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id='v1_payouts_list')
    def get(self, request):
        payments = PaymentService.list_payments(str(request.user.id))
        payouts = []
        for payment in payments:
            amount = Decimal(str(payment.get("amount") or 0)) * Decimal("0.9")
            payouts.append(
                {
                    "id": f"payout-{payment.get('payment_id')}",
                    "payment_id": payment.get("payment_id"),
                    "amount": float(amount),
                    "status": "processed" if payment.get("status") == "completed" else "pending",
                    "created_at": payment.get("created_at"),
                }
            )
        return Response({"payouts": payouts, "total": len(payouts)})


class PayoutDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id='v1_payouts_detail')
    def get(self, request, payout_id):
        payments = PaymentService.list_payments(str(request.user.id))
        for payment in payments:
            if f"payout-{payment.get('payment_id')}" == payout_id:
                amount = Decimal(str(payment.get("amount") or 0)) * Decimal("0.9")
                return Response(
                    {
                        "id": payout_id,
                        "payment_id": payment.get("payment_id"),
                        "amount": float(amount),
                        "status": "processed" if payment.get("status") == "completed" else "pending",
                        "created_at": payment.get("created_at"),
                    }
                )
        return Response({"detail": "Payout not found."}, status=status.HTTP_404_NOT_FOUND)


class WalletView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = PaymentService.list_payments(str(request.user.id))
        available = Decimal("0")
        pending = Decimal("0")
        for payment in payments:
            value = Decimal(str(payment.get("amount") or 0)) * Decimal("0.9")
            if payment.get("status") == "completed":
                available += value
            else:
                pending += value
        return Response({"currency": "KES", "available": float(available), "pending": float(pending)})


class RevenueReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = OrderService.list_orders(str(request.user.id), request.user.is_staff)
        total = sum(float(order.get("total_amount") or 0) for order in orders)
        return Response({"total_revenue": total, "orders_count": len(orders)})


class OrdersReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = OrderService.list_orders(str(request.user.id), request.user.is_staff)
        grouped = {}
        for order in orders:
            key = str(order.get("status") or "unknown")
            grouped[key] = grouped.get(key, 0) + 1
        return Response({"by_status": grouped, "total": len(orders)})


class ProductsReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = ProductService.get_products({})
        return Response(
            {
                "total_products": len(products),
                "in_stock": len([p for p in products if int(p.get("stock") or 0) > 0]),
                "low_stock": len([p for p in products if int(p.get("stock") or 0) <= 5]),
            }
        )


class CustomReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from_value = request.query_params.get("from")
        to_value = request.query_params.get("to")
        from_dt = _parse_iso(from_value)
        to_dt = _parse_iso(to_value)

        orders = OrderService.list_orders(str(request.user.id), request.user.is_staff)
        filtered = []
        for order in orders:
            order_dt = _parse_iso(order.get("order_date"))
            if not order_dt:
                continue
            if from_dt and order_dt < from_dt:
                continue
            if to_dt and order_dt > to_dt:
                continue
            filtered.append(order)

        total = sum(float(order.get("total_amount") or 0) for order in filtered)
        return Response({"from": from_value, "to": to_value, "orders": len(filtered), "revenue": total})


class ExportReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "export_url": "/api/v1/reports/export.csv",
                "detail": "CSV export generation is not yet asynchronous; use report endpoints for live data.",
            }
        )