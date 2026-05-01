import logging
import os
from dotenv import load_dotenv

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from supabase import create_client, Client

load_dotenv()

logger = logging.getLogger(__name__)


class SupabaseService:
    """Handles interactions with Supabase database."""

    _client: Client = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client instance."""
        if cls._client is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")

            if not url or not key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables"
                )

            cls._client = create_client(url, key)

        return cls._client
    @classmethod
    def create_user(cls, user_data: dict) -> dict:
        """Create a new user in Supabase users table."""
        client = cls.get_client()
        response = client.table('user').insert(user_data).execute()
        return response.data[0] if response.data else None

    @classmethod
    def get_user(cls, user_id: str) -> dict:
        """Get user by ID from Supabase."""
        client = cls.get_client()
        response = client.table('user').select('*').eq('user_id', user_id).execute()
        return response.data[0] if response.data else None

    @classmethod
    def update_user(cls, user_id: str, user_data: dict) -> dict:
        """Update user in Supabase."""
        client = cls.get_client()
        response = client.table('user').update(user_data).eq('user_id', user_id).execute()
        return response.data[0] if response.data else None

    @classmethod
    def delete_user(cls, user_id: str) -> bool:
        """Delete user from Supabase."""
        client = cls.get_client()
        response = client.table('user').delete().eq('user_id', user_id).execute()
        return len(response.data) > 0

    @classmethod
    def get_users(cls, filters: dict = None) -> list:
        """Get users with optional filters."""
        client = cls.get_client()
        query = client.table('user').select('*')
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        response = query.execute()
        return response.data


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
    def get_tokens_for_user(user) -> dict:
        """Generate JWT access and refresh tokens for the given user."""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    def logout(refresh_token: str) -> None:
        """Blacklist the given refresh token to invalidate the session."""
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info('Refresh token blacklisted.')
        except TokenError as exc:
            logger.warning('Logout attempt with invalid token: %s', exc)
            raise


class UserService:
    """Handles user profile and account state operations."""

    @staticmethod
    def update_profile(user, data: dict):
        """Apply validated field updates to the user model and persist."""
        for attr, value in data.items():
            setattr(user, attr, value)
        user.save()
        logger.info('Profile updated: %s', user.email)
        return user

    @staticmethod
    def change_password(user, new_password: str) -> None:
        """Hash and save a new password for the user."""
        user.set_password(new_password)
        user.save(update_fields=['password'])
        logger.info('Password changed: %s', user.email)

    @staticmethod
    def set_active(user, active: bool) -> None:
        """Activate or deactivate a user account."""
        user.is_active = active
        user.save(update_fields=['is_active'])
        state = 'activated' if active else 'deactivated'
        logger.info('User %s %s by admin.', user.email, state)


class AdminVendorService:
    """Handles admin vendor management operations."""

    @staticmethod
    def verify_vendor(vendor_profile, is_verified: bool, admin_user, notes: str = ''):
        """Verify or reject a vendor application."""
        from django.utils import timezone
        
        vendor_profile.is_verified = is_verified
        if is_verified:
            vendor_profile.verified_at = timezone.now()
        vendor_profile.save()
        
        # Log action
        AuditLogService.log_action(
            admin_user,
            'vendor_verify' if is_verified else 'vendor_reject',
            'vendor',
            vendor_profile.id,
            f'Vendor {"approved" if is_verified else "rejected"}. Notes: {notes}'
        )
        
        logger.info('Vendor %s %s by admin %s', 
                   vendor_profile.user.email, 
                   'verified' if is_verified else 'rejected',
                   admin_user.email)
        return vendor_profile

    @staticmethod
    def suspend_vendor(vendor_profile, reason: str, duration_days: int, admin_user):
        """Suspend a vendor account."""
        from datetime import timedelta
        from django.utils import timezone
        
        vendor_profile.is_suspended = True
        vendor_profile.suspension_reason = reason
        vendor_profile.suspended_at = timezone.now()
        vendor_profile.suspension_expires_at = timezone.now() + timedelta(days=duration_days)
        vendor_profile.save()
        
        # Log action
        AuditLogService.log_action(
            admin_user,
            'vendor_suspend',
            'vendor',
            vendor_profile.id,
            f'Suspended for {duration_days} days. Reason: {reason}'
        )
        
        logger.info('Vendor %s suspended by admin %s', 
                   vendor_profile.user.email,
                   admin_user.email)
        return vendor_profile

    @staticmethod
    def activate_vendor(vendor_profile, admin_user):
        """Reactivate a suspended vendor account."""
        from django.utils import timezone
        
        vendor_profile.is_suspended = False
        vendor_profile.suspension_reason = ''
        vendor_profile.suspended_at = None
        vendor_profile.suspension_expires_at = None
        vendor_profile.save()
        
        # Log action
        AuditLogService.log_action(
            admin_user,
            'vendor_activate',
            'vendor',
            vendor_profile.id,
            'Vendor reactivated'
        )
        
        logger.info('Vendor %s activated by admin %s', 
                   vendor_profile.user.email,
                   admin_user.email)
        return vendor_profile

    @staticmethod
    def assign_dropoff_station(vendor_profile, station_id, admin_user, reason: str = ''):
        """Assign a pickup station to vendor."""
        vendor_profile.default_dropoff_station_id = station_id
        vendor_profile.save()
        
        # Log action
        AuditLogService.log_action(
            admin_user,
            'other',
            'vendor',
            vendor_profile.id,
            f'Assigned pickup station {station_id}. Reason: {reason}'
        )
        
        logger.info('Vendor %s assigned to station %s by admin %s', 
                   vendor_profile.user.email,
                   station_id,
                   admin_user.email)
        return vendor_profile


class AuditLogService:
    """Handles admin audit logging."""

    @staticmethod
    def log_action(admin_user, action: str, target_type: str, target_id, 
                   details: str = '', ip_address: str = None):
        """Log an admin action for audit trail."""
        from users.models import AdminAuditLog
        
        log_entry = AdminAuditLog.objects.create(
            admin=admin_user,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address
        )
        
        logger.info('Admin action logged: %s by %s', action, admin_user.email)
        return log_entry

    @staticmethod
    def get_logs(admin_user=None, action=None, target_type=None, limit=100):
        """Retrieve audit logs with optional filters."""
        from users.models import AdminAuditLog
        
        query = AdminAuditLog.objects.all()
        
        if admin_user:
            query = query.filter(admin=admin_user)
        if action:
            query = query.filter(action=action)
        if target_type:
            query = query.filter(target_type=target_type)
        
        return query[:limit]
