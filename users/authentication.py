from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from django.core.exceptions import ImproperlyConfigured
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken

from tradelink_django.supabase_client import SupabaseService
from tradelink_django.supabase_postgrest import SupabaseAPIError


def _first_row(resp: Any) -> Optional[Dict[str, Any]]:
    data = getattr(resp, "data", resp)
    if isinstance(data, list):
        return data[0] if data else None
    if isinstance(data, dict):
        return data
    return None


@dataclass
class SupabaseUser:
    id: str
    email: str
    username: str
    role: str = "user"
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False

    first_name: str = ""
    last_name: str = ""
    phone_number: str = ""
    gender: str = ""

    password_hash: str = ""
    is_email_verified: bool = False

    @property
    def is_authenticated(self) -> bool:  # Django expects this
        return True

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "SupabaseUser":
        # Support both existing Supabase column naming and the repo's previous sync fields.
        email = row.get("email") or row.get("email_address") or ""
        username = row.get("username") or row.get("user_name") or ""

        first_name = row.get("first_name") or row.get("fname") or ""
        last_name = row.get("last_name") or row.get("lname") or ""

        return cls(
            id=str(row.get("user_id") or row.get("id") or ""),
            email=str(email),
            username=str(username),
            role=str(row.get("role") or "user"),
            is_active=bool(row.get("is_active", True)),
            is_staff=bool(row.get("is_staff", False)),
            is_superuser=bool(row.get("is_superuser", False)),
            first_name=str(first_name),
            last_name=str(last_name),
            phone_number=str(row.get("phone_number") or row.get("phone") or ""),
            gender=str(row.get("gender") or ""),
            password_hash=str(row.get("password_hash") or ""),
            is_email_verified=bool(row.get("is_email_verified", False)),
        )


class SupabaseJWTAuthentication(BaseAuthentication):
    """JWT auth that loads the authenticated user from Supabase (no Django auth/ORM)."""

    user_table = "user"
    user_id_claim = "user_id"

    def authenticate(self, request):
        raw = get_authorization_header(request).decode("utf-8")
        if not raw:
            return None

        parts = raw.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]
        try:
            validated_token = UntypedToken(token)
        except (InvalidToken, TokenError) as exc:
            raise AuthenticationFailed("Invalid token") from exc

        user = self.get_user(validated_token)
        return (user, validated_token)

    def get_user(self, validated_token):
        user_id = validated_token.get(self.user_id_claim) or validated_token.get("sub")
        if not user_id:
            raise AuthenticationFailed("Token contained no user id")

        client = SupabaseService.get_client()
        try:
            resp = client.table(self.user_table).select("*").eq("user_id", user_id).limit(1).execute()
        except SupabaseAPIError as exc:
            raise AuthenticationFailed("Failed to load user from Supabase") from exc
        row = _first_row(resp)
        if not row:
            raise AuthenticationFailed("User not found")

        user = SupabaseUser.from_row(row)
        if not user.id:
            raise ImproperlyConfigured(
                f"Supabase user table '{self.user_table}' must have a 'user_id' (uuid) column"
            )
        if not user.is_active:
            raise AuthenticationFailed("User is inactive")
        return user
