from typing import Any, Dict, List, Optional

from tradelink_django.supabase_client import SupabaseService


class ProductService:
	"""CRUD wrapper for the Supabase product table."""

	@classmethod
	def get_products(cls, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
		query = SupabaseService.get_client().table("product").select("*")
		if filters:
			if filters.get("category_id"):
				query = query.eq("category_id", filters["category_id"])
			if filters.get("in_stock"):
				query = query.gt("stock", 0)
			if filters.get("min_price") is not None:
				query = query.gte("price", filters["min_price"])
			if filters.get("max_price") is not None:
				query = query.lte("price", filters["max_price"])
			if filters.get("search"):
				term = f"%{filters['search']}%"
				query = query.or_(
					f"product_name.ilike.{term},product_description.ilike.{term}"
				)
		response = query.execute()
		return response.data or []

	@classmethod
	def get_product(cls, product_id: str) -> Optional[Dict[str, Any]]:
		response = (
			SupabaseService.get_client()
			.table("product")
			.select("*")
			.eq("product_id", product_id)
			.execute()
		)
		return response.data[0] if response.data else None

	@classmethod
	def create_product(cls, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		response = SupabaseService.get_client().table("product").insert(payload).execute()
		return response.data[0] if response.data else None

	@classmethod
	def update_product(cls, product_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		response = (
			SupabaseService.get_client()
			.table("product")
			.update(payload)
			.eq("product_id", product_id)
			.execute()
		)
		return response.data[0] if response.data else None

	@classmethod
	def delete_product(cls, product_id: str) -> bool:
		response = (
			SupabaseService.get_client()
			.table("product")
			.delete()
			.eq("product_id", product_id)
			.execute()
		)
		return bool(response.data)





