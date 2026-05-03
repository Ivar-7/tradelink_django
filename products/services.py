from typing import Any, Dict, List, Optional
from tradelink_django.supabase_client import SupabaseService

class ProductService:
    """CRUD wrapper for the Supabase product table."""

    @classmethod
    def _create_stock_for_product(cls, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        payload = {
            "product_id": product.get("product_id"),
            "vendor_id": product.get("vendor_id"),
            "quantity": int(product.get("stock") or 0),
            "price": product.get("price") or 0,
            "is_flash_sale": False,
            "discount_percentage": 0,
        }
        response = SupabaseService.get_client().table("stock").insert(payload).execute()
        return response.data[0] if response.data else None

    @classmethod
    def get_stock(cls, stock_id: str) -> Optional[Dict[str, Any]]:
        response = (
            SupabaseService.get_client()
            .table("stock")
            .select("*")
            .eq("stock_id", stock_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    @classmethod
    def get_stock_by_product(cls, product_id: str) -> Optional[Dict[str, Any]]:
        response = (
            SupabaseService.get_client()
            .table("stock")
            .select("*")
            .eq("product_id", product_id)
            .order("last_updated", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    @classmethod
    def resolve_stock_id(cls, product_or_stock_id: str) -> Optional[str]:
        stock = cls.get_stock(product_or_stock_id)
        if stock:
            return str(stock.get("stock_id"))

        stock = cls.get_stock_by_product(product_or_stock_id)
        if stock:
            return str(stock.get("stock_id"))

        product = cls.get_product(product_or_stock_id)
        if product:
            created_stock = cls._create_stock_for_product(product)
            if created_stock:
                return str(created_stock.get("stock_id"))

        return None

    @classmethod
    def get_product_for_stock(cls, stock_id: str) -> Optional[Dict[str, Any]]:
        stock = cls.get_stock(stock_id)
        if not stock:
            return None

        product = cls.get_product(str(stock.get("product_id")))
        if not product:
            return None

        merged = dict(product)
        merged["stock_id"] = stock.get("stock_id")
        merged["product_id"] = stock.get("product_id")
        merged["price"] = stock.get("price", product.get("price"))
        merged["stock_quantity"] = stock.get("quantity", 0)
        return merged

    @classmethod
    def get_products(cls, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        verified_only = bool((filters or {}).get("verified_only"))
        if verified_only:
            # Only products from verified vendors.
            # Requires FK: product.vendor_id -> vendor_profile.vendor_id
            query = SupabaseService.get_client().table("product").select("*,vendor_profile!inner(is_verified)")
            query = query.eq("vendor_profile.is_verified", "true")
        else:
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
        
        # 🔥 TRIGGER ADDED: automatically create the stock row if the product successfully creates
        created_product = response.data[0] if response.data else None
        if created_product:
            cls._create_stock_for_product(created_product)
            
        return created_product

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