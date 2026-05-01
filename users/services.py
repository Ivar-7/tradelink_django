import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from tradelink_django.supabase_client import SupabaseService
from tradelink_django.supabase_postgrest import SupabaseAPIError

logger = logging.getLogger(__name__)


def _first_row(resp: Any) -> Optional[Dict[str, Any]]:
    data = getattr(resp, "data", resp)
    if isinstance(data, list):
        return data[0] if data else None
    if isinstance(data, dict):
        return data
    return None


class SupabaseUserService:
    """DB access layer for the Supabase `user` table (HTTP only)."""

    table = "user"

    @classmethod
    def get_client(cls):
        return SupabaseService.get_client()

    @classmethod
    def create_user(cls, user_data: Dict[str, Any]) -> Dict[str, Any]:
        client = cls.get_client()
        resp = client.table(cls.table).insert(user_data).execute()
        row = _first_row(resp)
        if not row:
            raise SupabaseAPIError("User creation returned no row")
        return row

    @classmethod
    def get_user_by_id(cls, user_id: str) -> Optional[Dict[str, Any]]:
        client = cls.get_client()
        resp = client.table(cls.table).select("*").eq("user_id", user_id).limit(1).execute()
        return _first_row(resp)

    @classmethod
    def get_user_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        client = cls.get_client()
        resp = client.table(cls.table).select("*").eq("email", email).limit(1).execute()
        return _first_row(resp)

    @classmethod
    def get_user_by_username(cls, username: str) -> Optional[Dict[str, Any]]:
        client = cls.get_client()
        resp = client.table(cls.table).select("*").eq("username", username).limit(1).execute()
        return _first_row(resp)

    @classmethod
    def get_user_by_verification_token(cls, token: str) -> Optional[Dict[str, Any]]:
        client = cls.get_client()
        resp = (
            client.table(cls.table)
            .select("*")
            .eq("email_verification_token", token)
            .limit(1)
            .execute()
        )
        return _first_row(resp)

    @classmethod
    def get_user_by_reset_token(cls, token: str) -> Optional[Dict[str, Any]]:
        client = cls.get_client()
        resp = (
            client.table(cls.table)
            .select("*")
            .eq("password_reset_token", token)
            .limit(1)
            .execute()
        )
        return _first_row(resp)

    @classmethod
    def update_user(cls, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        client = cls.get_client()
        resp = client.table(cls.table).update(user_data).eq("user_id", user_id).execute()
        row = _first_row(resp)
        if not row:
            # PostgREST returns [] if no row matched. Treat as not found.
            raise SupabaseAPIError("User update returned no row")
        return row

    @classmethod
    def delete_user(cls, user_id: str) -> bool:
        client = cls.get_client()
        resp = client.table(cls.table).delete().eq("user_id", user_id).execute()
        data = getattr(resp, "data", resp)
        return bool(data)

    @classmethod
    def list_users(cls, filters: Optional[Dict[str, Any]] = None) -> list:
        client = cls.get_client()
        query = client.table(cls.table).select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        resp = query.execute()
        return getattr(resp, "data", [])

    @classmethod
    def verify_password(cls, user_row: Dict[str, Any], password: str) -> bool:
        password_hash = user_row.get("password_hash") or ""
        if not password_hash:
            return False
        return check_password(password, password_hash)

    @classmethod
    def set_password(cls, user_id: str, new_password: str) -> Dict[str, Any]:
        return cls.update_user(user_id, {"password_hash": make_password(new_password)})


class SupabaseVendorService:
    table = "vendor_profile"

    @classmethod
    def get_client(cls):
        return SupabaseService.get_client()

    @classmethod
    def get_vendor_profile(cls, vendor_id: str) -> Optional[Dict[str, Any]]:
        client = cls.get_client()
        resp = client.table(cls.table).select("*").eq("vendor_id", vendor_id).limit(1).execute()
        return _first_row(resp)

    @classmethod
    def create_vendor_profile(
        cls,
        *,
        user_id: str,
        vendor_type: str,
        business_name: str,
        verification_doc_url: str,
    ) -> Dict[str, Any]:
        client = cls.get_client()
        payload = {
            "user_id": user_id,
            "vendor_type": vendor_type,
            "verification_doc_url": verification_doc_url,
            "is_verified": False,
        }
        resp = client.table(cls.table).insert(payload).execute()
        row = _first_row(resp)
        if not row:
            raise SupabaseAPIError("Vendor creation returned no row")
        return row

    @classmethod
    def list_vendor_profiles(cls) -> list:
        client = cls.get_client()
        resp = client.table(cls.table).select("*").execute()
        return getattr(resp, "data", [])

    @classmethod
    def update_vendor_profile(cls, vendor_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        client = cls.get_client()
        resp = client.table(cls.table).update(patch).eq("vendor_id", vendor_id).execute()
        row = _first_row(resp)
        if not row:
            raise SupabaseAPIError("Vendor update returned no row")
        return row


class CartService:
    """Handles interactions with Supabase cart table."""

    @classmethod
    def get_client(cls):
        return SupabaseService.get_client()

    @classmethod
    def create_cart(cls, cart_data: dict) -> dict:
        """Create a new cart."""
        client = cls.get_client()
        response = client.table('cart').insert(cart_data).execute()
        return response.data[0] if response.data else None

    @classmethod
    def get_cart(cls, cart_id: str) -> dict:
        """Get cart by ID."""
        client = cls.get_client()
        response = client.table('cart').select('*').eq('cart_id', cart_id).execute()
        return response.data[0] if response.data else None

    @classmethod
    def get_user_cart(cls, user_id: str) -> dict:
        """Get active cart for user."""
        client = cls.get_client()
        response = client.table('cart').select('*').eq('user_id', user_id).execute()
        return response.data[0] if response.data else None


class CartItemService:
    """Handles interactions with Supabase cart_item table."""

    @classmethod
    def get_client(cls):
        return SupabaseService.get_client()

    @classmethod
    def add_item(cls, item_data: dict) -> dict:
        """Add item to cart."""
        client = cls.get_client()
        response = client.table('cart_item').insert(item_data).execute()
        return response.data[0] if response.data else None

    @classmethod
    def get_cart_items(cls, cart_id: str) -> list:
        """Get all items in a cart."""
        client = cls.get_client()
        response = client.table('cart_item').select('*').eq('cart_id', cart_id).execute()
        return response.data


class OrderService:
    """Handles interactions with Supabase orders table."""

    @classmethod
    def get_client(cls):
        return SupabaseService.get_client()

    @classmethod
    def create_order(cls, order_data: dict) -> dict:
        """Create a new order."""
        client = cls.get_client()
        response = client.table('orders').insert(order_data).execute()
        return response.data[0] if response.data else None

    @classmethod
    def get_user_orders(cls, user_id: str) -> list:
        """Get orders for a user."""
        client = cls.get_client()
        response = client.table('orders').select('*').eq('user_id', user_id).execute()
        return response.data


class ProductService:
    """Handles interactions with Supabase product table."""

    @classmethod
    def get_client(cls):
        return SupabaseService.get_client()

    @classmethod
    def get_products(cls, category_id: str = None) -> list:
        """Get products, optionally filtered by category."""
        client = cls.get_client()
        query = client.table('product').select('*')
        if category_id:
            query = query.eq('category_id', category_id)
        response = query.execute()
        return response.data

    @classmethod
    def get_product(cls, product_id: str) -> dict:
        """Get product by ID."""
        client = cls.get_client()
        response = client.table('product').select('*').eq('product_id', product_id).execute()
        return response.data[0] if response.data else None


class ReviewService:
    """Handles interactions with Supabase review table."""

    @classmethod
    def get_client(cls):
        return SupabaseService.get_client()

    @classmethod
    def create_review(cls, review_data: dict) -> dict:
        """Create a new review."""
        client = cls.get_client()
        response = client.table('review').insert(review_data).execute()
        return response.data[0] if response.data else None

    @classmethod
    def get_product_reviews(cls, product_id: str) -> list:
        """Get reviews for a product."""
        client = cls.get_client()
        response = client.table('review').select('*').eq('product_id', product_id).execute()
        return response.data


class AddressService:
    """Handles interactions with Supabase delivery_address table."""

    @classmethod
    def get_client(cls):
        return SupabaseService.get_client()

    @classmethod
    def create_address(cls, address_data: dict) -> dict:
        """Create a new delivery address."""
        client = cls.get_client()
        response = client.table('delivery_address').insert(address_data).execute()
        return response.data[0] if response.data else None

    @classmethod
    def get_user_addresses(cls, user_id: str) -> list:
        """Get addresses for a user."""
        client = cls.get_client()
        response = client.table('delivery_address').select('*').eq('user_id', user_id).execute()
        return response.data


class AuthService:
    """Handles JWT token operations."""

    @staticmethod
    def get_tokens_for_user(user_row: Dict[str, Any]) -> dict:
        """Generate JWT access and refresh tokens for a Supabase user row."""
        refresh = RefreshToken()
        refresh["user_id"] = str(user_row.get("user_id") or user_row.get("id"))
        refresh["email"] = user_row.get("email")
        refresh["username"] = user_row.get("username")
        refresh["role"] = user_row.get("role")

        access = refresh.access_token
        access["user_id"] = refresh["user_id"]
        access["email"] = refresh.get("email")
        access["username"] = refresh.get("username")
        access["role"] = refresh.get("role")

        return {
            "refresh": str(refresh),
            "access": str(access),
        }

    @staticmethod
    def logout(refresh_token: str) -> None:
        """Client-side logout.

        Token blacklisting requires persistent storage; this codebase intentionally does not.
        """
        if not refresh_token:
            return
        try:
            RefreshToken(refresh_token)
        except Exception:
            return


class UserService:
    """Handles user profile and account state operations."""

    @staticmethod
    def update_profile(user, data: dict):
        """Apply validated field updates to the Supabase user record."""
        user_id = getattr(user, "id", None) or getattr(user, "user_id", None)
        updated = SupabaseUserService.update_user(str(user_id), data)
        logger.info("Profile updated: %s", updated.get("email"))
        return updated

    @staticmethod
    def change_password(user, new_password: str) -> None:
        user_id = getattr(user, "id", None) or getattr(user, "user_id", None)
        SupabaseUserService.set_password(str(user_id), new_password)
        logger.info("Password changed for user_id=%s", user_id)

    @staticmethod
    def set_active(user, active: bool) -> None:
        user_id = getattr(user, "id", None) or getattr(user, "user_id", None)
        SupabaseUserService.update_user(str(user_id), {"is_active": bool(active)})
        state = "activated" if active else "deactivated"
        logger.info("User %s %s by admin.", user_id, state)


class AdminVendorService:
    """Handles admin vendor management operations."""

    @staticmethod
    def verify_vendor(vendor_profile: Dict[str, Any], is_verified: bool, admin_user, notes: str = ''):
        """Verify or reject a vendor application."""
        vendor_id = str(vendor_profile.get("vendor_id") or vendor_profile.get("id"))
        vendor_profile = SupabaseVendorService.update_vendor_profile(
            vendor_id,
            {"is_verified": bool(is_verified)},
        )
        
        # Log action
        AuditLogService.log_action(
            admin_user,
            'vendor_verify' if is_verified else 'vendor_reject',
            'vendor',
            vendor_id,
            f'Vendor {"approved" if is_verified else "rejected"}. Notes: {notes}'
        )
        
        logger.info(
            "Vendor %s %s by admin %s",
            vendor_id,
            "verified" if is_verified else "rejected",
            getattr(admin_user, "email", "admin"),
        )
        return vendor_profile

    @staticmethod
    def suspend_vendor(vendor_profile: Dict[str, Any], reason: str, duration_days: int, admin_user):
        """Suspend a vendor account.

        Current Supabase schema does not include vendor suspension fields on vendor_profile;
        we model suspension by deactivating the underlying user.
        """
        vendor_id = str(vendor_profile.get("vendor_id") or vendor_profile.get("id"))
        user_id = str(vendor_profile.get("user_id") or "")
        if user_id:
            SupabaseUserService.update_user(user_id, {"is_active": False})
        
        # Log action
        AuditLogService.log_action(
            admin_user,
            'vendor_suspend',
            'vendor',
            vendor_id,
            f'Suspended for {duration_days} days. Reason: {reason}'
        )
        
        logger.info(
            "Vendor %s suspended by admin %s",
            vendor_id,
            getattr(admin_user, "email", "admin"),
        )
        return vendor_profile

    @staticmethod
    def activate_vendor(vendor_profile: Dict[str, Any], admin_user):
        """Reactivate a vendor account by activating the underlying user."""
        vendor_id = str(vendor_profile.get("vendor_id") or vendor_profile.get("id"))
        user_id = str(vendor_profile.get("user_id") or "")
        if user_id:
            SupabaseUserService.update_user(user_id, {"is_active": True})
        
        # Log action
        AuditLogService.log_action(
            admin_user,
            'vendor_activate',
            'vendor',
            vendor_id,
            'Vendor reactivated'
        )
        
        logger.info(
            "Vendor %s activated by admin %s",
            vendor_id,
            getattr(admin_user, "email", "admin"),
        )
        return vendor_profile

    @staticmethod
    def assign_dropoff_station(vendor_profile: Dict[str, Any], station_id, admin_user, reason: str = ''):
        """Assign a pickup station to vendor."""
        vendor_id = str(vendor_profile.get("vendor_id") or vendor_profile.get("id"))
        vendor_profile = SupabaseVendorService.update_vendor_profile(
            vendor_id,
            {"default_dropoff_station_id": station_id},
        )
        
        # Log action
        AuditLogService.log_action(
            admin_user,
            'other',
            'vendor',
            vendor_id,
            f'Assigned pickup station {station_id}. Reason: {reason}'
        )
        
        logger.info(
            "Vendor %s assigned to station %s by admin %s",
            vendor_id,
            station_id,
            getattr(admin_user, "email", "admin"),
        )
        return vendor_profile


class AuditLogService:
    """Handles admin audit logging."""

    @staticmethod
    def log_action(admin_user, action: str, target_type: str, target_id, 
                   details: str = '', ip_address: str = None):
        """Log an admin action for audit trail.

        This codebase does not persist audit logs in Django ORM.
        If you have a Supabase table for audit logs, wire it here.
        """
        logger.info(
            "Admin action: %s target=%s:%s admin=%s ip=%s details=%s",
            action,
            target_type,
            target_id,
            getattr(admin_user, "email", "admin"),
            ip_address,
            details,
        )
        return {
            "action": action,
            "target_type": target_type,
            "target_id": str(target_id),
            "details": details,
            "ip_address": ip_address,
        }

    @staticmethod
    def get_logs(admin_user=None, action=None, target_type=None, limit=100):
        return []
