from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from tradelink_django.supabase_client import SupabaseService


def default_vendor_application(user_id: str):
    return {
        "user_id": user_id,
        "business_name": "",
        "business_email": "",
        "business_phone": "",
        "tax_id": "",
        "status": "draft",
        "submitted_at": None,
        "reviewed_at": None,
        "review_notes": "",
    }


def parse_iso(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


class _VendorApplicationStore:
    """Drop-in replacement for VENDOR_APPLICATIONS dict."""

    def _fetch(self, user_id: str) -> Optional[Dict[str, Any]]:
        response = (
            SupabaseService.get_client()
            .table("vendor_applications")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def __getitem__(self, user_id: str) -> Dict[str, Any]:
        app = self._fetch(user_id)
        if app is None:
            raise KeyError(user_id)
        return app

    def __setitem__(self, user_id: str, value: Dict[str, Any]) -> None:
        existing = self._fetch(user_id)
        if existing:
            SupabaseService.get_client().table("vendor_applications").update(value).eq(
                "user_id", user_id
            ).execute()
        else:
            SupabaseService.get_client().table("vendor_applications").insert(value).execute()

    def get(self, user_id: str, default=None):
        app = self._fetch(user_id)
        return app if app is not None else default

    def __contains__(self, user_id: str) -> bool:
        return self._fetch(user_id) is not None

    def values(self) -> List[Dict[str, Any]]:
        response = (
            SupabaseService.get_client().table("vendor_applications").select("*").execute()
        )
        return response.data or []

    def keys(self) -> List[str]:
        return [app["user_id"] for app in self.values()]

    def items(self) -> List[tuple]:
        return [(app["user_id"], app) for app in self.values()]


class _DictStore:
    """Generic dict-like Supabase backed store."""

    def __init__(
        self,
        table_name: str,
        key_column: str,
        key_resolver: Optional[Callable[[str], Optional[str]]] = None,
    ):
        self.table_name = table_name
        self.key_column = key_column
        self.key_resolver = key_resolver

    def _resolve_key(self, key: str) -> str:
        if self.key_resolver:
            resolved = self.key_resolver(key)
            if resolved is None:
                raise KeyError(f"Could not resolve key '{key}' via {self.key_resolver.__name__}")
            return resolved
        return key

    def _fetch(self, key: str) -> Optional[Dict[str, Any]]:
        resolved_key = self._resolve_key(key)
        response = (
            SupabaseService.get_client()
            .table(self.table_name)
            .select("*")
            .eq(self.key_column, resolved_key)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def __getitem__(self, key: str) -> Dict[str, Any]:
        item = self._fetch(key)
        if item is None:
            raise KeyError(key)
        return item

    def __setitem__(self, key: str, value: Dict[str, Any]) -> None:
        resolved_key = self._resolve_key(key)
        existing = self._fetch(key)
        if existing:
            SupabaseService.get_client().table(self.table_name).update(value).eq(
                self.key_column, resolved_key
            ).execute()
        else:
            payload = {**value, self.key_column: resolved_key}
            SupabaseService.get_client().table(self.table_name).insert(payload).execute()

    def get(self, key: str, default=None):
        item = self._fetch(key)
        return item if item is not None else default

    def __contains__(self, key: str) -> bool:
        return self._fetch(key) is not None

    def values(self) -> List[Dict[str, Any]]:
        response = SupabaseService.get_client().table(self.table_name).select("*").execute()
        return response.data or []

    def keys(self) -> List[str]:
        return [item[self.key_column] for item in self.values()]

    def items(self) -> List[tuple]:
        return [(item[self.key_column], item) for item in self.values()]


def _resolve_vendor_id(user_id: str) -> Optional[str]:
    """Map user_id -> vendor_id via vendor_profile."""
    response = (
        SupabaseService.get_client()
        .table("vendor_profile")
        .select("vendor_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if response.data:
        return str(response.data[0]["vendor_id"])
    return None


# Drop-in replacements — your existing views can keep using these
VENDOR_APPLICATIONS = _VendorApplicationStore()
STORE_PROFILES = _DictStore("vendor_store", "vendor_id", key_resolver=_resolve_vendor_id)
USER_SETTINGS = _DictStore("user_settings", "user_id")
USER_NOTIFICATIONS = _DictStore("user_notifications", "user_id")