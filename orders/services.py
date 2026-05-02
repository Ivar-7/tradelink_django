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
