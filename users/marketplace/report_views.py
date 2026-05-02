from datetime import datetime, timezone
from decimal import Decimal

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as s
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.services import OrderService
from products.services import ProductService

from .shared import parse_iso


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Vendor dashboard summary (orders, revenue, top products)",
        responses=inline_serializer(
            name="DashboardSummaryResponse",
            fields={
                "revenueToday": s.FloatField(),
                "ordersToday": s.IntegerField(),
                "pendingOrders": s.IntegerField(),
                "lowStockCount": s.IntegerField(),
                "topProducts": s.ListField(child=s.DictField()),
                "recentOrders": s.ListField(child=s.DictField()),
            },
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

            order_date = parse_iso(order.get("order_date"))
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
        from_dt = parse_iso(from_value)
        to_dt = parse_iso(to_value)

        orders = OrderService.list_orders(str(request.user.id), request.user.is_staff)
        filtered = []
        for order in orders:
            order_dt = parse_iso(order.get("order_date"))
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
