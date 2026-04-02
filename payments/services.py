from typing import Any, Dict, List, Optional

from tradelink_django.supabase_client import SupabaseService


class PaymentService:
    @classmethod
    def create_payment(cls, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        response = SupabaseService.get_client().table("payment").insert(payload).execute()
        return response.data[0] if response.data else None

    @classmethod
    def get_payment(cls, payment_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        response = (
            SupabaseService.get_client()
            .table("payment")
            .select("*")
            .eq("payment_id", payment_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    @classmethod
    def list_payments(cls, user_id: str) -> List[Dict[str, Any]]:
        response = (
            SupabaseService.get_client()
            .table("payment")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        return response.data or []
