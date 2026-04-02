from typing import Any, Dict, List, Optional

from tradelink_django.supabase_client import SupabaseService


class FeedbackService:
    @classmethod
    def create_feedback(cls, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        response = SupabaseService.get_client().table("user_feedback").insert(payload).execute()
        return response.data[0] if response.data else None

    @classmethod
    def list_feedback(cls, user_id: str) -> List[Dict[str, Any]]:
        response = (
            SupabaseService.get_client()
            .table("user_feedback")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        return response.data or []
