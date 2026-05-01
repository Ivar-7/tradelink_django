import os

from dotenv import load_dotenv
from tradelink_django.supabase_postgrest import SupabasePostgrestClient

load_dotenv()


class SupabaseService:
    """Shared Supabase client factory used across apps."""

    _client: SupabasePostgrestClient | None = None

    @classmethod
    def get_client(cls) -> SupabasePostgrestClient:
        if cls._client is None:
            url = os.getenv("SUPABASE_URL")
            if not url:
                raise ValueError(
                    "SUPABASE_URL must be set in environment variables"
                )
            cls._client = SupabasePostgrestClient()
        return cls._client
