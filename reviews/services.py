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


class Products:
    """Service for CRUD operations on products table in Supabase."""

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
    def create_review(cls, product_id: str, user_id: str, rating_value: int, comment: Optional[str] = None) -> Dict[str, Any]:
        """Create a new review."""
        client = cls.get_client()
        data = {
            "product_id": product_id,
            "user_id": user_id,
            "rating_value": rating_value,
            "comment": comment
        }
        response = client.table("review").insert(data).execute()
        result = cls._handle_response(response)
        return result[0] if result else {}      
        
        

    @classmethod
    def get_review(cls, product_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single review by ID."""
        client = cls.get_client()
        response = client.table("review").select("*").eq("product_id", product_id).execute()
        result = cls._handle_response(response)
        return result[0] if result else None

    @classmethod
    def list_reviews(cls) -> List[Dict[str, Any]]:
        """Retrieve all reviews."""
        client = cls.get_client()
        response = client.table("review").select("*").execute()
        result = cls._handle_response(response)
        return result if result else []

    @classmethod
    def update_review(cls, product_id: str, user_id: str, rating_value: int, comment: Optional[str] = None) -> Dict[str, Any]:
        """Fully update a review (PUT)."""
        client = cls.get_client()
        data = {
            "product_id": product_id,
            "user_id": user_id,
            "rating_value": rating_value,
            "comment": comment
        }
        response = client.table("review").update(data).eq("product_id", product_id).execute()
        result = cls._handle_response(response)
        return result[0] if result else {}
        

    @classmethod
    def partial_update_review(cls, product_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update a review (PATCH)."""
        client = cls.get_client()
        response = client.table("review").update(data).eq("product_id", product_id).execute()
        result = cls._handle_response(response)
        return result[0] if result else {}

    @classmethod
    def delete_review(cls, product_id: str) -> bool:
        """Delete a review by ID."""
        client = cls.get_client()
        response = client.table("review").delete().eq("product_id", product_id).execute()
        result = cls._handle_response(response)
        return bool(result)