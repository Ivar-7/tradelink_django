import uuid
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
from .services import (
    DeliveryAddressService, 
    OrderItemService, 
    OrderService,
    # New services required for the updated flow
    OrderSuborderService,
    ShipmentService,
    OrderStatusHistoryService,
    InventoryService
)


class OrderViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _serialize_order(order):
        items = OrderItemService.list_order_items(order["order_id"])
        suborders = OrderSuborderService.get_suborders(order["order_id"])
        shipment = ShipmentService.get_shipment(order["order_id"])
        
        return {
            "id": order.get("order_id"),
            "user_id": order.get("user_id"),
            "order_date": order.get("order_date"),
            "order_amount": order.get("total_amount"),
            "products": [
                {
                    "product_id": i.get("stock_id"),
                    "vendor_id": i.get("vendor_id"),
                    "quantity": i.get("quantity"),
                    "unit_price": i.get("unit_price"),
                    "subtotal": (i.get("quantity") or 0) * float(i.get("unit_price") or 0),
                }
                for i in items
            ],
            "suborders": suborders,
            "status": order.get("status"),
            "shipping_method": order.get("shipping_type"),
            "tracking": {
                "tracking_number": shipment.get("tracking_number") if shipment else None,
                "shipment_status": shipment.get("status") if shipment else None,
                "pickup_time": shipment.get("pickup_time") if shipment else None,
            },
            "delivery_address": order.get("delivery_address"),
            "cancellation_reason": order.get("cancellation_reason", ""),
        }

    # ==========================================
    # BUYER ENDPOINTS
    # ==========================================

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
        vendor_totals = {}

        # 1. Validate Products & Group by Vendor
        for item in items_data:
            # AFTER
            raw_id = str(item["product_id"])

            # Try resolving as stock_id first, then fall back to product_id
            stock_record = ProductService.get_stock(raw_id)

            if stock_record:
                # It's a stock_id — fetch enriched product+stock data
                product = ProductService.get_product_for_stock(raw_id)
                stock_id = raw_id
            else:
                # It's a product_id — look up or create the stock record
                product = ProductService.get_product(raw_id)
                resolved_stock_id = ProductService.resolve_stock_id(raw_id)
                stock_id = resolved_stock_id

            if not product:
                return Response({"detail": "Product not found."}, status=status.HTTP_400_BAD_REQUEST)

            qty = int(item["quantity"])
            unit_price = float(product.get("price") or 0)
            vendor_id = product.get("vendor_id")
            
            subtotal = unit_price * qty
            total_amount += subtotal
            
            # Track suborder totals
            if vendor_id:
                vendor_totals[vendor_id] = vendor_totals.get(vendor_id, 0.0) + subtotal

            order_items.append(
                {
                    "stock_id": stock_id,
                    "vendor_id": vendor_id,
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

        # Handle Address
        address_data = serializer.validated_data.get("delivery_address")
        if address_data:
            address = DeliveryAddressService.create_address({
                "user_id": user_id,
                "country": "Kenya",
                "county": address_data.get("county"),
                "city": address_data.get("city"),
                "postal_address": address_data.get("postal_address"),
                "contact_phone": address_data.get("user_contact"),
            })
            if address:
                order_payload["address_id"] = address.get("address_id")

        # 2. Master Order
        order = OrderService.create_order(order_payload)
        if not order:
            return Response({"detail": "Failed to create order."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        order_id = order["order_id"]

        # 3. Order Items
        OrderItemService.create_items([
            {"order_id": order_id, **item} for item in order_items
        ])

        # 4. Order Suborders (Per Vendor)
        for v_id, sub_amount in vendor_totals.items():
            OrderSuborderService.create_suborder({
                "order_id": order_id,
                "vendor_id": v_id,
                "subtotal": sub_amount,
                "status": "pending"
            })

        # 5. Shipment Tracking Record
        tracking_number = f"TRK-{str(uuid.uuid4())[:8].upper()}"
        ShipmentService.create_shipment({
            "order_id": order_id,
            "tracking_number": tracking_number,
            "status": "pending"
        })

        # 6. Audit Trail (History)
        OrderStatusHistoryService.log_change({
            "order_id": order_id,
            "old_status": "created",
            "new_status": "pending",
            "changed_by": user_id,
            "changed_by_role": "buyer",
            "notes": "Order placed"
        })

        # Clear Cart
        cart = CartService.get_cart_by_user(user_id)
        if cart:
            CartItemService.clear(cart["cart_id"])
            CartService.update_total(cart["cart_id"])

        return Response(self._serialize_order(order), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def tracking(self, request, pk=None):
        """Fetch the full timeline/audit history of the order."""
        order = OrderService.get_order(pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        
        history = OrderStatusHistoryService.get_history(pk)
        return Response({"order_id": pk, "timeline": history}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="confirm-delivery")
    def confirm_delivery(self, request, pk=None):
        """Buyer confirms they have received the package."""
        order = OrderService.get_order(pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if order.get("status") == "delivered":
            return Response({"detail": "Order already delivered."}, status=status.HTTP_400_BAD_REQUEST)

        now = datetime.now(timezone.utc).isoformat()
        
        # Update Master Order
        updated = OrderService.update_order(pk, {"status": "delivered"})
        
        # Update Suborders & Shipment
        OrderSuborderService.update_status_by_order(pk, "delivered")
        ShipmentService.update_status(pk, "delivered", pickup_time=now)

        # Audit Log
        OrderStatusHistoryService.log_change({
            "order_id": pk,
            "old_status": order.get("status"),
            "new_status": "delivered",
            "changed_by": str(request.user.id),
            "changed_by_role": "buyer",
            "notes": "Buyer confirmed delivery"
        })

        return Response(self._serialize_order(updated), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = OrderService.get_order(pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        if order.get("status") in ["shipped", "out_for_delivery", "delivered", "cancelled"]:
            return Response(
                {"detail": f"Cannot cancel order with status {order.get('status')}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"]

        updated = OrderService.update_order(pk, {
            "status": "cancelled",
            "cancellation_reason": reason,
        })
        OrderSuborderService.update_status_by_order(pk, "cancelled")
        ShipmentService.update_status(pk, "cancelled")

        OrderStatusHistoryService.log_change({
            "order_id": pk,
            "old_status": order.get("status"),
            "new_status": "cancelled",
            "changed_by": str(request.user.id),
            "changed_by_role": "buyer",
            "notes": f"Cancelled: {reason}"
        })

        return Response(self._serialize_order(updated), status=status.HTTP_200_OK)

    # ==========================================
    # VENDOR ENDPOINTS
    # ==========================================

    @action(detail=True, methods=["post"], url_path="vendor-accept")
    def vendor_accept(self, request, pk=None):
        """Vendor accepts their portion of the order."""
        # Typically requires validating that request.user.id matches the vendor_id
        vendor_id = request.data.get("vendor_id") 
        suborder = OrderSuborderService.get_vendor_suborder(pk, vendor_id)
        
        if not suborder:
            return Response({"detail": "Suborder not found."}, status=status.HTTP_404_NOT_FOUND)

        OrderSuborderService.update_suborder(suborder["suborder_id"], {"status": "processing"})
        
        OrderStatusHistoryService.log_change({
            "order_id": pk,
            "suborder_id": suborder["suborder_id"],
            "old_status": suborder.get("status"),
            "new_status": "processing",
            "changed_by": str(request.user.id),
            "changed_by_role": "vendor",
            "notes": "Vendor accepted order"
        })

        return Response({"detail": "Order accepted for processing."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="vendor-ship")
    def vendor_ship(self, request, pk=None):
        """Vendor marks the package as shipped/handed to courier."""
        vendor_id = request.data.get("vendor_id")
        suborder = OrderSuborderService.get_vendor_suborder(pk, vendor_id)
        
        if not suborder:
            return Response({"detail": "Suborder not found."}, status=status.HTTP_404_NOT_FOUND)

        # 1. Update Suborder
        OrderSuborderService.update_suborder(suborder["suborder_id"], {"status": "shipped"})
        
        # 2. Update Master Order & Shipment (If all suborders are shipped, master is shipped)
        all_shipped = OrderSuborderService.check_all_shipped(pk)
        if all_shipped:
            OrderService.update_order(pk, {"status": "shipped"})
            ShipmentService.update_status(pk, "in_transit")

        # 3. Deduct Stock Inventory & Log Movement
        items = OrderItemService.list_order_items(pk)
        for item in items:
            if item.get("vendor_id") == vendor_id:
                InventoryService.record_movement(
                    stock_id=item["stock_id"],
                    movement_type="sale",
                    quantity_change=-abs(item["quantity"]),
                    reference_id=pk
                )

        # 4. Audit Log
        OrderStatusHistoryService.log_change({
            "order_id": pk,
            "suborder_id": suborder["suborder_id"],
            "old_status": suborder.get("status"),
            "new_status": "shipped",
            "changed_by": str(request.user.id),
            "changed_by_role": "vendor",
            "notes": "Package handed to courier"
        })

        return Response({"detail": "Suborder marked as shipped."}, status=status.HTTP_200_OK)

    # ==========================================
    # ADMIN / COURIER ENDPOINTS
    # ==========================================

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        """Admin/Courier updates arbitrary order status."""
        order = OrderService.get_order(pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status")
        valid_statuses = {"new", "pending", "processing", "shipped", "out_for_delivery", "delivered", "cancelled"}
        if new_status not in valid_statuses:
            return Response(
                {"detail": f"Invalid status. Use one of {', '.join(valid_statuses)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = OrderService.update_order(pk, {"status": new_status})
        
        # Sync Shipment Status if applicable
        if new_status in ["shipped", "out_for_delivery"]:
            ShipmentService.update_status(pk, new_status)

        OrderStatusHistoryService.log_change({
            "order_id": pk,
            "old_status": order.get("status"),
            "new_status": new_status,
            "changed_by": str(request.user.id),
            "changed_by_role": "admin",
            "notes": request.data.get("notes", "Status updated by admin")
        })

        return Response(self._serialize_order(updated), status=status.HTTP_200_OK)