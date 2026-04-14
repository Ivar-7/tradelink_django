import logging
from typing import Any, Dict, List, Optional

from django.db import DatabaseError

from product_categories.models import ProductCategory
from tradelink_django.supabase_client import SupabaseService


logger = logging.getLogger(__name__)


class ProductCategoryService:
    """Service for CRUD operations on product_category table in Supabase."""

    @staticmethod
    def _to_payload(category: ProductCategory) -> Dict[str, Any]:
        return {
            "category_id": str(category.id),
            "name": category.name,
            "description": category.description,
            "image_url": category.image_url,
            "parent_id": str(category.parent_id) if category.parent_id else None,
            "sort_order": category.sort_order,
        }

    @classmethod
    def _list_from_local_db(cls) -> List[Dict[str, Any]]:
        try:
            return [cls._to_payload(item) for item in ProductCategory.objects.all().order_by("name")]
        except DatabaseError as exc:
            logger.warning("Local category fallback unavailable due to schema mismatch: %s", exc)
            return []

    @classmethod
    def create_category(
        cls,
        name: str,
        description: Optional[str] = None,
        parent_id: Optional[str] = None,
        sort_order: int = 0,
    ) -> Dict[str, Any]:
        """Create a new product category."""
        client = SupabaseService.get_client()
        data = {
            "name": name,
            "description": description,
            "parent_id": parent_id,
            "sort_order": sort_order,
        }
        response = client.table("product_category").insert(data).execute()
        return response.data[0] if response.data else {}

    @classmethod
    def get_category(cls, category_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single category by ID."""
        try:
            client = SupabaseService.get_client()
            response = client.table("product_category").select("*").eq("category_id", category_id).execute()
            if response.data:
                return response.data[0]
        except Exception as exc:
            logger.warning("Supabase get_category failed, using local DB fallback: %s", exc)

        try:
            local = ProductCategory.objects.filter(id=category_id).first()
        except DatabaseError as exc:
            logger.warning("Local category get fallback unavailable: %s", exc)
            return None
        return cls._to_payload(local) if local else None

    @classmethod
    def list_categories(cls) -> List[Dict[str, Any]]:
        """Retrieve all categories."""
        local_items = cls._list_from_local_db()

        try:
            client = SupabaseService.get_client()
            response = client.table("product_category").select("*").execute()
            remote_items = response.data or []

            if not remote_items:
                logger.info("Supabase returned zero categories, using local DB fallback.")
                return local_items

            # Merge remote + local in dev to keep frontend data stable.
            merged = []
            seen_names = set()
            for item in [*remote_items, *local_items]:
                name = str(item.get("name") or "").strip().lower()
                key = name or str(item.get("category_id") or "")
                if key and key in seen_names:
                    continue
                if key:
                    seen_names.add(key)
                merged.append(item)
            return merged
        except Exception as exc:
            logger.warning("Supabase list_categories failed, using local DB fallback: %s", exc)

        return local_items

    @classmethod
    def update_category(
        cls,
        category_id: str,
        name: str,
        description: Optional[str] = None,
        parent_id: Optional[str] = None,
        sort_order: int = 0,
    ) -> Dict[str, Any]:
        """Fully update a category (PUT)."""
        client = SupabaseService.get_client()
        data = {
            "name": name,
            "description": description,
            "parent_id": parent_id,
            "sort_order": sort_order,
        }
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