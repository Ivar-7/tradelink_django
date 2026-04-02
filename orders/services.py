from typing import Any, Dict, List, Optional

from tradelink_django.supabase_client import SupabaseService


class OrderService:
    @classmethod
    def list_orders(cls, user_id: str = "", is_admin: bool = False) -> List[Dict[str, Any]]:
        query = SupabaseService.get_client().table("orders").select("*")
        if not is_admin:
            query = query.eq("user_id", user_id)
        response = query.order("order_date", desc=True).execute()
        return response.data or []

    @classmethod
    def get_order(cls, order_id: str) -> Optional[Dict[str, Any]]:
        response = (
            SupabaseService.get_client()
            .table("orders")
            .select("*")
            .eq("order_id", order_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    @classmethod
    def create_order(cls, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        response = SupabaseService.get_client().table("orders").insert(payload).execute()
        return response.data[0] if response.data else None

    @classmethod
    def update_order(cls, order_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        response = (
            SupabaseService.get_client()
            .table("orders")
            .update(payload)
            .eq("order_id", order_id)
            .execute()
        )
        return response.data[0] if response.data else None


class OrderItemService:
    @classmethod
    def create_items(cls, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not items:
            return []
        response = SupabaseService.get_client().table("order_item").insert(items).execute()
        return response.data or []

    @classmethod
    def list_order_items(cls, order_id: str) -> List[Dict[str, Any]]:
        response = (
            SupabaseService.get_client()
            .table("order_item")
            .select("*")
            .eq("order_id", order_id)
            .execute()
        )
        return response.data or []


class DeliveryAddressService:
    @classmethod
    def create_address(cls, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        response = SupabaseService.get_client().table("delivery_address").insert(payload).execute()
        return response.data[0] if response.data else None
