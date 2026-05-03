from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tradelink_django.supabase_client import SupabaseService


def _first_row(resp: Any) -> Optional[Dict[str, Any]]:
    data = getattr(resp, "data", resp)
    if isinstance(data, list):
        return data[0] if data else None
    if isinstance(data, dict):
        return data
    return None


class DeliveryAddressService:
    table = "delivery_address"

    @classmethod
    def create_address(cls, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        resp = SupabaseService.get_client().table(cls.table).insert(payload).execute()
        return _first_row(resp)


class OrderService:
    table = "orders"

    @classmethod
    def list_orders(cls, user_id: str, is_admin: bool = False) -> List[Dict[str, Any]]:
        query = SupabaseService.get_client().table(cls.table).select("*")
        if not is_admin:
            query = query.eq("user_id", user_id)
        resp = query.order("order_date", desc=True).execute()
        return resp.data or []

    @classmethod
    def get_order(cls, order_id: str) -> Optional[Dict[str, Any]]:
        resp = (
            SupabaseService.get_client()
            .table(cls.table)
            .select("*")
            .eq("order_id", order_id)
            .limit(1)
            .execute()
        )
        return _first_row(resp)

    @classmethod
    def create_order(cls, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        resp = SupabaseService.get_client().table(cls.table).insert(payload).execute()
        return _first_row(resp)

    @classmethod
    def update_order(cls, order_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        resp = (
            SupabaseService.get_client()
            .table(cls.table)
            .update(patch)
            .eq("order_id", order_id)
            .execute()
        )
        return _first_row(resp)


class OrderItemService:
    table = "order_item"

    @classmethod
    def list_order_items(cls, order_id: str) -> List[Dict[str, Any]]:
        resp = (
            SupabaseService.get_client()
            .table(cls.table)
            .select("*")
            .eq("order_id", order_id)
            .execute()
        )
        return resp.data or []

    @classmethod
    def create_items(cls, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not items:
            return []
        resp = SupabaseService.get_client().table(cls.table).insert(items).execute()
        return resp.data or []


class OrderSuborderService:
    table = "order_suborder"

    @classmethod
    def create_suborder(cls, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        resp = SupabaseService.get_client().table(cls.table).insert(payload).execute()
        return _first_row(resp)

    @classmethod
    def get_suborders(cls, order_id: str) -> List[Dict[str, Any]]:
        resp = (
            SupabaseService.get_client()
            .table(cls.table)
            .select("*")
            .eq("order_id", order_id)
            .execute()
        )
        return resp.data or []

    @classmethod
    def get_vendor_suborder(cls, order_id: str, vendor_id: str) -> Optional[Dict[str, Any]]:
        resp = (
            SupabaseService.get_client()
            .table(cls.table)
            .select("*")
            .eq("order_id", order_id)
            .eq("vendor_id", vendor_id)
            .limit(1)
            .execute()
        )
        return _first_row(resp)

    @classmethod
    def update_suborder(cls, suborder_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        resp = (
            SupabaseService.get_client()
            .table(cls.table)
            .update(patch)
            .eq("suborder_id", suborder_id)
            .execute()
        )
        return _first_row(resp)

    @classmethod
    def update_status_by_order(cls, order_id: str, status: str) -> List[Dict[str, Any]]:
        """Updates all suborders belonging to a master order (used for bulk cancellations/deliveries)"""
        resp = (
            SupabaseService.get_client()
            .table(cls.table)
            .update({"status": status})
            .eq("order_id", order_id)
            .execute()
        )
        return resp.data or []

    @classmethod
    def check_all_shipped(cls, order_id: str) -> bool:
        """Checks if all vendor suborders for a master order are marked as shipped or delivered."""
        suborders = cls.get_suborders(order_id)
        if not suborders:
            return False
        return all(sub.get("status") in ["shipped", "delivered"] for sub in suborders)


class ShipmentService:
    table = "shipment"

    @classmethod
    def create_shipment(cls, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        resp = SupabaseService.get_client().table(cls.table).insert(payload).execute()
        return _first_row(resp)

    @classmethod
    def get_shipment(cls, order_id: str) -> Optional[Dict[str, Any]]:
        resp = (
            SupabaseService.get_client()
            .table(cls.table)
            .select("*")
            .eq("order_id", order_id)
            .limit(1)
            .execute()
        )
        return _first_row(resp)

    @classmethod
    def update_status(cls, order_id: str, status: str, pickup_time: Optional[str] = None) -> Optional[Dict[str, Any]]:
        patch = {
            "status": status,
            "last_update_time": datetime.now(timezone.utc).isoformat()
        }
        # If your schema gets a pickup_time column later, you can map it here.
        
        resp = (
            SupabaseService.get_client()
            .table(cls.table)
            .update(patch)
            .eq("order_id", order_id)
            .execute()
        )
        return _first_row(resp)


class OrderStatusHistoryService:
    table = "order_status_history"

    @classmethod
    def log_change(cls, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        resp = SupabaseService.get_client().table(cls.table).insert(payload).execute()
        return _first_row(resp)

    @classmethod
    def get_history(cls, order_id: str) -> List[Dict[str, Any]]:
        resp = (
            SupabaseService.get_client()
            .table(cls.table)
            .select("*")
            .eq("order_id", order_id)
            .order("created_at", desc=False)
            .execute()
        )
        return resp.data or []


class InventoryService:
    movement_table = "inventory_movement"
    stock_table = "stock"

    @classmethod
    def record_movement(cls, stock_id: str, movement_type: str, quantity_change: int, reference_id: str) -> Optional[Dict[str, Any]]:
        client = SupabaseService.get_client()
        
        # 1. Fetch current stock quantity
        stock_resp = client.table(cls.stock_table).select("quantity").eq("stock_id", stock_id).limit(1).execute()
        current_stock = _first_row(stock_resp)
        
        prev_qty = current_stock.get("quantity", 0) if current_stock else 0
        new_qty = prev_qty + quantity_change
        
        # 2. Update stock table
        client.table(cls.stock_table).update({"quantity": new_qty}).eq("stock_id", stock_id).execute()
        
        # 3. Log the inventory movement
        movement_payload = {
            "stock_id": stock_id,
            "movement_type": movement_type,
            "quantity_change": quantity_change,
            "previous_quantity": prev_qty,
            "new_quantity": new_qty,
            "reference_id": reference_id
        }
        resp = client.table(cls.movement_table).insert(movement_payload).execute()
        return _first_row(resp)