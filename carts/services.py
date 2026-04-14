from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from django.contrib.auth import get_user_model
from postgrest.exceptions import APIError

from tradelink_django.supabase_client import SupabaseService


class CartService:
    @classmethod
    def _resolve_supabase_user_id(cls, user_id: str, user: Optional[Any] = None) -> str:
        client = SupabaseService.get_client()
        existing_user = client.table("user").select("user_id").eq("user_id", user_id).limit(1).execute()
        if existing_user.data:
            return user_id

        local_user = user
        if local_user is None:
            local_user = get_user_model().objects.filter(id=user_id).first()

        if local_user is None:
            # No local user record to sync from; keep original user_id and let caller fail loudly.
            return user_id

        existing_by_email = (
            client.table("user")
            .select("user_id")
            .eq("email_address", local_user.email)
            .limit(1)
            .execute()
        )
        if existing_by_email.data:
            return str(existing_by_email.data[0]["user_id"])

        payload = {
            "user_id": user_id,
            "username": local_user.username,
            "fname": local_user.first_name or "",
            "lname": local_user.last_name or "",
            "email_address": local_user.email,
            "password_hash": local_user.password,
            "gender": local_user.gender or None,
            "role": local_user.role,
        }
        client.table("user").insert(payload).execute()
        return user_id

    @classmethod
    def get_or_create_cart(cls, user: Union[str, Any]) -> Dict[str, Any]:
        user_id = str(user.id) if hasattr(user, "id") else str(user)
        supabase_user_id = cls._resolve_supabase_user_id(user_id, user if hasattr(user, "id") else None)
        client = SupabaseService.get_client()
        existing = client.table("cart").select("*").eq("user_id", supabase_user_id).limit(1).execute()
        if existing.data:
            return existing.data[0]

        try:
            created = client.table("cart").insert({"user_id": supabase_user_id, "total_price": 0}).execute()
        except APIError as exc:
            payload = exc.args[0] if exc.args and isinstance(exc.args[0], dict) else {}
            if payload.get("code") == "23503" and "cart_user_id_fkey" in payload.get("message", ""):
                supabase_user_id = cls._resolve_supabase_user_id(
                    user_id, user if hasattr(user, "id") else None
                )
                created = client.table("cart").insert({"user_id": supabase_user_id, "total_price": 0}).execute()
            else:
                raise

        return created.data[0]

    @classmethod
    def get_cart_by_user(cls, user_id: str) -> Optional[Dict[str, Any]]:
        response = (
            SupabaseService.get_client()
            .table("cart")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    @classmethod
    def update_total(cls, cart_id: str) -> Decimal:
        items = CartItemService.list_items(cart_id)
        from products.services import ProductService

        total = Decimal("0")
        for item in items:
            product = ProductService.get_product_for_stock(item.get("stock_id"))
            price = Decimal(str(product.get("price") if product else 0))
            qty = Decimal(str(item.get("quantity") or 0))
            total += price * qty
        SupabaseService.get_client().table("cart").update({"total_price": float(total)}).eq(
            "cart_id", cart_id
        ).execute()
        return total

    @classmethod
    def set_total(cls, cart_id: str, total: float) -> None:
        SupabaseService.get_client().table("cart").update({"total_price": float(total)}).eq(
            "cart_id", cart_id
        ).execute()


class CartItemService:
    @classmethod
    def list_items(cls, cart_id: str) -> List[Dict[str, Any]]:
        response = (
            SupabaseService.get_client()
            .table("cart_item")
            .select("*")
            .eq("cart_id", cart_id)
            .execute()
        )
        return response.data or []

    @classmethod
    def get_item(cls, cart_item_id: str) -> Optional[Dict[str, Any]]:
        response = (
            SupabaseService.get_client()
            .table("cart_item")
            .select("*")
            .eq("cart_item_id", cart_item_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    @classmethod
    def add_or_increment_item(
        cls, cart_id: str, stock_id: str, quantity: int, unit_price: Any
    ) -> Dict[str, Any]:
        client = SupabaseService.get_client()
        existing = (
            client.table("cart_item")
            .select("*")
            .eq("cart_id", cart_id)
            .eq("stock_id", stock_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            row = existing.data[0]
            new_quantity = int(row.get("quantity") or 0) + quantity
            updated = (
                client.table("cart_item")
                .update({"quantity": new_quantity})
                .eq("cart_item_id", row["cart_item_id"])
                .execute()
            )
            return updated.data[0]

        created = (
            client.table("cart_item")
            .insert(
                {
                    "cart_id": cart_id,
                    "stock_id": stock_id,
                    "quantity": quantity,
                }
            )
            .execute()
        )
        return created.data[0]

    @classmethod
    def update_quantity(cls, cart_item_id: str, quantity: int) -> Optional[Dict[str, Any]]:
        response = (
            SupabaseService.get_client()
            .table("cart_item")
            .update({"quantity": quantity})
            .eq("cart_item_id", cart_item_id)
            .execute()
        )
        return response.data[0] if response.data else None

    @classmethod
    def delete_item(cls, cart_item_id: str) -> bool:
        response = (
            SupabaseService.get_client()
            .table("cart_item")
            .delete()
            .eq("cart_item_id", cart_item_id)
            .execute()
        )
        return bool(response.data)

    @classmethod
    def clear(cls, cart_id: str) -> None:
        SupabaseService.get_client().table("cart_item").delete().eq("cart_id", cart_id).execute()
