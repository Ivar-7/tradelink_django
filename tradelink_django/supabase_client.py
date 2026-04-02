import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


class SupabaseService:
    """Shared Supabase client factory used across apps."""

    _client: Client | None = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._client is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")
            if not url or not key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables"
                )
            cls._client = create_client(url, key)
        return cls._client
