from datetime import datetime, timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from carts.services import CartItemService, CartService
from products.services import ProductService
from .serializers import (
    OrderCancelSerializer,
    OrderCreateSerializer,
    OrderIssueCreateSerializer,
    ReturnRequestCreateSerializer,
)
from .services import DeliveryAddressService, OrderItemService, OrderService


class OrderViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _serialize_order(order):
        items = OrderItemService.list_order_items(order["order_id"])
        return {
            "id": order.get("order_id"),
            "user_id": order.get("user_id"),
            "order_date": order.get("order_date"),
            "order_amount": order.get("total_amount"),
            "products": [
                {
                    "product_id": i.get("stock_id"),
                    "quantity": i.get("quantity"),
                    "unit_price": i.get("unit_price"),
                    "subtotal": (i.get("quantity") or 0) * float(i.get("unit_price") or 0),
                }
                for i in items
            ],
            "status": order.get("status"),
            "shipping_method": order.get("shipping_type"),
            "tracking_number": order.get("tracking_number"),
            "delivered_at": order.get("delivered_at"),
            "cancelled_at": order.get("cancelled_at"),
            "cancellation_reason": order.get("cancellation_reason", ""),
            "issue_report": order.get("issue_report"),
            "return_request": order.get("return_request"),
            "delivery_address": order.get("delivery_address"),
        }

    @extend_schema(operation_id='v1_orders_list')
    def list(self, request):
        orders = OrderService.list_orders(str(request.user.id), request.user.is_staff)
        status_filter = request.query_params.get("status")
        if status_filter and status_filter != "all":
            orders = [o for o in orders if o.get("status") == status_filter]

        serialized = [self._serialize_order(order) for order in orders]
        return Response({"orders": serialized, "total": len(serialized)})

    @extend_schema(operation_id='v1_orders_detail')
    def retrieve(self, request, pk=None):
        order = OrderService.get_order(pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_staff and order.get("user_id") != str(request.user.id):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self._serialize_order(order))

    def create(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = str(request.user.id)
        items_data = serializer.validated_data.get("products") or []

        if not items_data:
            cart = CartService.get_cart_by_user(user_id)
            if cart:
                cart_items = CartItemService.list_items(cart["cart_id"])
                items_data = [
                    {"product_id": item.get("stock_id"), "quantity": item.get("quantity", 1)}
                    for item in cart_items
                ]

        if not items_data:
            return Response({"detail": "No items to order."}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = 0.0
        order_items = []
        for item in items_data:
            product = ProductService.get_product(str(item["product_id"]))
            if not product:
                return Response({"detail": "Product not found."}, status=status.HTTP_400_BAD_REQUEST)
            qty = int(item["quantity"])
            unit_price = float(product.get("price") or 0)
            total_amount += unit_price * qty
            order_items.append(
                {
                    "stock_id": str(item["product_id"]),
                    "quantity": qty,
                    "unit_price": unit_price,
                }
            )

        shipping_method = serializer.validated_data["shipping_method"]
        order_payload = {
            "user_id": user_id,
            "shipping_type": shipping_method,
            "total_amount": total_amount,
            "status": "pending",
            "order_date": datetime.now(timezone.utc).isoformat(),
        }

        address_data = serializer.validated_data.get("delivery_address")
        if address_data:
            address = DeliveryAddressService.create_address(
                {
                    "user_id": user_id,
                    "country": "Kenya",
                    "county": address_data.get("county"),
                    "city": address_data.get("city"),
                    "postal_address": address_data.get("postal_address"),
                    "contact_phone": address_data.get("user_contact"),
                }
            )
            if address:
                order_payload["address_id"] = address.get("address_id")
                order_payload["delivery_address"] = address_data

        order = OrderService.create_order(order_payload)
        if not order:
            return Response({"detail": "Failed to create order."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        OrderItemService.create_items([
            {"order_id": order["order_id"], **item} for item in order_items
        ])

        cart = CartService.get_cart_by_user(user_id)
        if cart:
            CartItemService.clear(cart["cart_id"])
            CartService.update_total(cart["cart_id"])

        return Response(self._serialize_order(order), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        order = OrderService.get_order(pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        if order.get("status") == "cancelled":
            return Response({"detail": "Cannot confirm a cancelled order."}, status=status.HTTP_400_BAD_REQUEST)

        updated = OrderService.update_order(
            pk,
            {"status": "delivered", "delivered_at": datetime.now(timezone.utc).isoformat()},
        )
        return Response(self._serialize_order(updated), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = OrderService.get_order(pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        if order.get("status") in ["shipped", "delivered", "cancelled"]:
            return Response(
                {"detail": f"Cannot cancel order with status {order.get('status')}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = OrderService.update_order(
            pk,
            {
                "status": "cancelled",
                "cancelled_at": datetime.now(timezone.utc).isoformat(),
                "cancellation_reason": serializer.validated_data["reason"],
            },
        )
        return Response(self._serialize_order(updated), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def issue(self, request, pk=None):
        order = OrderService.get_order(pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderIssueCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {
                "detail": "Order issue reporting is not yet mapped to a Supabase table.",
                "type": serializer.validated_data["type"],
                "details": serializer.validated_data["details"],
                "order_id": pk,
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    @action(detail=True, methods=["post"])
    def request_return(self, request, pk=None):
        order = OrderService.get_order(pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReturnRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {
                "detail": "Return requests are not yet mapped to a Supabase table.",
                "reason": serializer.validated_data["reason"],
                "notes": serializer.validated_data.get("notes", ""),
                "order_id": pk,
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        order = OrderService.get_order(pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status")
        valid_statuses = {"new", "pending", "confirmed", "packed", "shipped", "delivered", "cancelled"}
        if new_status not in valid_statuses:
            return Response(
                {"detail": "Invalid status. Use one of new, pending, confirmed, packed, shipped, delivered, cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = {"status": new_status}
        if new_status == "delivered":
            payload["delivered_at"] = datetime.now(timezone.utc).isoformat()
        if new_status == "cancelled":
            payload["cancelled_at"] = datetime.now(timezone.utc).isoformat()
            payload["cancellation_reason"] = request.data.get("reason", "Cancelled by vendor")

        updated = OrderService.update_order(pk, payload)
        return Response(self._serialize_order(updated), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="refund")
    def refund(self, request, pk=None):
        order = OrderService.get_order(pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        updated = OrderService.update_order(
            pk,
            {
                "status": "cancelled",
                "cancelled_at": datetime.now(timezone.utc).isoformat(),
                "cancellation_reason": request.data.get("reason", "Refund processed"),
            },
        )
        return Response(
            {
                "detail": "Refund recorded.",
                "order": self._serialize_order(updated),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="ship")
    def ship(self, request, pk=None):
        order = OrderService.get_order(pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        if str(order.get("status")).lower() in {"cancelled", "delivered"}:
            return Response({"detail": "Order cannot be shipped in current state."}, status=status.HTTP_400_BAD_REQUEST)

        tracking_number = request.data.get("tracking_number") or f"TRK-{pk}"
        updated = OrderService.update_order(
            pk,
            {
                "status": "shipped",
                "tracking_number": tracking_number,
            },
        )
        return Response(self._serialize_order(updated), status=status.HTTP_200_OK)
