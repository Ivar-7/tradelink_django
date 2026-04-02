from typing import Any, Dict, List, Optional

from tradelink_django.supabase_client import SupabaseService


class ProductCategoryService:
    """Service for CRUD operations on product_category table in Supabase."""

    @classmethod
    def create_category(cls, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new product category."""
        client = SupabaseService.get_client()
        data = {"name": name, "description": description}
        response = client.table("product_category").insert(data).execute()
        return response.data[0] if response.data else {}

    @classmethod
    def get_category(cls, category_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single category by ID."""
        client = SupabaseService.get_client()
        response = client.table("product_category").select("*").eq("category_id", category_id).execute()
        return response.data[0] if response.data else None

    @classmethod
    def list_categories(cls) -> List[Dict[str, Any]]:
        """Retrieve all categories."""
        client = SupabaseService.get_client()
        response = client.table("product_category").select("*").execute()
        return response.data if response.data else []

    @classmethod
    def update_category(cls, category_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Fully update a category (PUT)."""
        client = SupabaseService.get_client()
        data = {"name": name, "description": description}
        response = client.table("product_category").update(data).eq("category_id", category_id).execute()
        return response.data[0] if response.data else {}

    @classmethod
    def partial_update_category(cls, category_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update a category (PATCH)."""
        client = SupabaseService.get_client()
        response = client.table("product_category").update(data).eq("category_id", category_id).execute()
        return response.data[0] if response.data else {}

    @classmethod
    def delete_category(cls, category_id: str) -> bool:
        """Delete a category by ID."""
        client = SupabaseService.get_client()
        response = client.table("product_category").delete().eq("category_id", category_id).execute()
        return bool(response.data)