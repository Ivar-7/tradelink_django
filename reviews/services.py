from typing import Any, Dict, List, Optional

from tradelink_django.supabase_client import SupabaseService


class ReviewService:
    """Service for CRUD operations on review table in Supabase."""

    @classmethod
    def create_review(cls, product_id: str, user_id: str, rating_value: int, comment: Optional[str] = None) -> Dict[str, Any]:
        """Create a new review."""
        client = SupabaseService.get_client()
        data = {
            "product_id": product_id,
            "user_id": user_id,
            "rating_value": rating_value,
            "comment": comment
        }
        response = client.table("review").insert(data).execute()
        return response.data[0] if response.data else {}

    @classmethod
    def get_review(cls, review_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single review by ID."""
        client = SupabaseService.get_client()
        response = client.table("review").select("*").eq("review_id", review_id).execute()
        return response.data[0] if response.data else None

    @classmethod
    def list_reviews(cls) -> List[Dict[str, Any]]:
        """Retrieve all reviews."""
        client = SupabaseService.get_client()
        response = client.table("review").select("*").execute()
        return response.data if response.data else []

    @classmethod
    def update_review(
        cls,
        review_id: str,
        product_id: str,
        user_id: str,
        rating_value: int,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fully update a review (PUT)."""
        client = SupabaseService.get_client()
        data = {
            "product_id": product_id,
            "user_id": user_id,
            "rating_value": rating_value,
            "comment": comment
        }
        response = client.table("review").update(data).eq("review_id", review_id).execute()
        return response.data[0] if response.data else {}

    @classmethod
    def partial_update_review(cls, review_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update a review (PATCH)."""
        client = SupabaseService.get_client()
        response = client.table("review").update(data).eq("review_id", review_id).execute()
        return response.data[0] if response.data else {}

    @classmethod
    def delete_review(cls, review_id: str) -> bool:
        """Delete a review by ID."""
        client = SupabaseService.get_client()
        response = client.table("review").delete().eq("review_id", review_id).execute()
        return bool(response.data)