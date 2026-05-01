import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import httpx


Json = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


class SupabaseAPIError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        details: Optional[Json] = None,
        response_text: Optional[str] = None,
        url: Optional[str] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.details = details
        self.response_text = response_text
        self.url = url


@dataclass
class SupabaseResponse:
    data: Any
    status_code: int
    headers: Dict[str, str]


def _pick_supabase_key() -> str:
    # Prefer service role for server-side operations; fall back to anon key.
    # Keep backwards-compat for a misspelled env var used in this repo.
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASER_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or ""
    ).strip()
    if not key:
        raise ValueError(
            "SUPABASE_SERVICE_ROLE_KEY (recommended) or SUPABASE_ANON_KEY must be set"
        )
    return key


def _supabase_rest_base_url() -> str:
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    if not url:
        raise ValueError("SUPABASE_URL must be set")
    return f"{url}/rest/v1"


def _parse_error_payload(payload: Any) -> Tuple[str, Optional[Json]]:
    if isinstance(payload, dict):
        # Common PostgREST/Supabase shapes
        msg = (
            payload.get("message")
            or payload.get("error")
            or payload.get("hint")
            or "Supabase request failed"
        )
        return str(msg), payload
    if isinstance(payload, list):
        return "Supabase request failed", payload
    if isinstance(payload, str):
        return payload, None
    return "Supabase request failed", None


class _TableQuery:
    def __init__(self, client: "SupabasePostgrestClient", table: str):
        self._client = client
        self._table = table
        self._method: str = "GET"
        self._select: Optional[str] = None
        self._filters: List[Tuple[str, str]] = []
        self._order: Optional[str] = None
        self._limit: Optional[int] = None
        self._payload: Optional[Json] = None

    def select(self, columns: str = "*") -> "_TableQuery":
        self._method = "GET"
        self._select = columns
        return self

    def insert(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> "_TableQuery":
        self._method = "POST"
        self._payload = data
        return self

    def update(self, data: Dict[str, Any]) -> "_TableQuery":
        self._method = "PATCH"
        self._payload = data
        return self

    def delete(self) -> "_TableQuery":
        self._method = "DELETE"
        self._payload = None
        return self

    def eq(self, column: str, value: Any) -> "_TableQuery":
        self._filters.append((column, f"eq.{value}"))
        return self

    def gt(self, column: str, value: Any) -> "_TableQuery":
        self._filters.append((column, f"gt.{value}"))
        return self

    def gte(self, column: str, value: Any) -> "_TableQuery":
        self._filters.append((column, f"gte.{value}"))
        return self

    def lt(self, column: str, value: Any) -> "_TableQuery":
        self._filters.append((column, f"lt.{value}"))
        return self

    def lte(self, column: str, value: Any) -> "_TableQuery":
        self._filters.append((column, f"lte.{value}"))
        return self

    def ilike(self, column: str, pattern: str) -> "_TableQuery":
        self._filters.append((column, f"ilike.{pattern}"))
        return self

    def in_(self, column: str, values: Iterable[Any]) -> "_TableQuery":
        joined = ",".join(str(v) for v in values)
        self._filters.append((column, f"in.({joined})"))
        return self

    def or_(self, expression: str) -> "_TableQuery":
        # Expression is already in PostgREST syntax.
        self._filters.append(("or", f"({expression})"))
        return self

    def order(self, column: str, desc: bool = False) -> "_TableQuery":
        self._order = f"{column}.{'desc' if desc else 'asc'}"
        return self

    def limit(self, n: int) -> "_TableQuery":
        self._limit = int(n)
        return self

    def execute(self) -> SupabaseResponse:
        params: List[Tuple[str, str]] = []
        if self._select is not None:
            params.append(("select", self._select))
        params.extend(self._filters)
        if self._order is not None:
            params.append(("order", self._order))
        if self._limit is not None:
            params.append(("limit", str(self._limit)))

        return self._client._request(
            method=self._method,
            path=f"/{self._table}",
            params=params,
            json=self._payload,
            prefer_return_representation=self._method in {"POST", "PATCH", "DELETE"},
        )


class SupabasePostgrestClient:
    """Minimal PostgREST client that mimics the supabase-py `table(...).select().eq()...execute()` style.

    This keeps most existing service code intact while enforcing the architecture:
    Django -> HTTP -> Supabase PostgREST -> Postgres.
    """

    def __init__(self, *, timeout: float = 30.0):
        self._base_url = _supabase_rest_base_url()
        self._key = _pick_supabase_key()
        self._timeout = timeout

    def table(self, name: str) -> _TableQuery:
        return _TableQuery(self, name)

    def rpc(self, fn: str, params: Optional[Dict[str, Any]] = None) -> SupabaseResponse:
        return self._request(
            method="POST",
            path=f"/rpc/{fn}",
            params=[],
            json=params or {},
            prefer_return_representation=True,
        )

    def _request(
        self,
        *,
        method: str,
        path: str,
        params: List[Tuple[str, str]],
        json: Optional[Json],
        prefer_return_representation: bool,
    ) -> SupabaseResponse:
        url = f"{self._base_url}{path}"
        headers = {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        }
        if prefer_return_representation:
            headers["Prefer"] = "return=representation"

        try:
            resp = httpx.request(
                method,
                url,
                params=params,
                json=json,
                headers=headers,
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            raise SupabaseAPIError(
                "Supabase request failed",
                url=url,
                response_text=str(exc),
            ) from exc

        content_type = (resp.headers.get("content-type") or "").lower()
        payload: Any
        if "application/json" in content_type:
            try:
                payload = resp.json()
            except ValueError:
                payload = resp.text
        else:
            payload = resp.text

        if resp.status_code >= 400:
            msg, details = _parse_error_payload(payload)
            raise SupabaseAPIError(
                msg,
                status_code=resp.status_code,
                details=details,
                response_text=resp.text,
                url=str(resp.url),
            )

        return SupabaseResponse(
            data=payload,
            status_code=resp.status_code,
            headers={k: v for k, v in resp.headers.items()},
        )
