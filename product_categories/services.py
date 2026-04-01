# product_category_service.py

import os
import logging
from typing import Optional, Dict, Any, List

from supabase import create_client, Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()  # Load credentials from .env

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")


class ProductCategoryService:
    """Service for CRUD operations on product_category table in Supabase."""

    _client: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create the Supabase client."""
        if cls._client is None:
            if not SUPABASE_URL or not SUPABASE_ANON_KEY:
                raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
            cls._client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        return cls._client

    @classmethod
    def _handle_response(cls, response) -> Any:
        """Check Supabase response and raise an exception if there is an error."""
        if not hasattr(response, "data"):
            raise Exception(f"Invalid response from Supabase: {response}")
        # Supabase returns status_code for success/failure
        if getattr(response, "status_code", 200) >= 400:
            logger.error(f"Supabase operation failed: {response.data}")
            raise Exception(f"Supabase error: {response.data}")
        return response.data

    @classmethod
    def create_category(cls, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new product category."""
        client = cls.get_client()
        data = {"name": name, "description": description}
        response = client.table("product_category").insert(data).execute()
        result = cls._handle_response(response)
        return result[0] if result else {}

    @classmethod
    def get_category(cls, category_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single category by ID."""
        client = cls.get_client()
        response = client.table("product_category").select("*").eq("category_id", category_id).execute()
        result = cls._handle_response(response)
        return result[0] if result else None

    @classmethod
    def list_categories(cls) -> List[Dict[str, Any]]:
        """Retrieve all categories."""
        client = cls.get_client()
        response = client.table("product_category").select("*").execute()
        result = cls._handle_response(response)
        return result if result else []

    @classmethod
    def update_category(cls, category_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Fully update a category (PUT)."""
        client = cls.get_client()
        data = {"name": name, "description": description}
        response = client.table("product_category").update(data).eq("category_id", category_id).execute()
        result = cls._handle_response(response)
        return result[0] if result else {}

    @classmethod
    def partial_update_category(cls, category_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update a category (PATCH)."""
        client = cls.get_client()
        response = client.table("product_category").update(data).eq("category_id", category_id).execute()
        result = cls._handle_response(response)
        return result[0] if result else {}

    @classmethod
    def delete_category(cls, category_id: str) -> bool:
        """Delete a category by ID."""
        client = cls.get_client()
        response = client.table("product_category").delete().eq("category_id", category_id).execute()
        result = cls._handle_response(response)
        return bool(result)