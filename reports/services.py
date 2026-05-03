import httpx
from django.conf import settings

class SupabaseRestClient:
    def __init__(self):
        self.base_url = f"{settings.SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        }

    def rpc(self, function_name: str, params: dict):
        """Call a Postgres function via Supabase RPC."""
        url = f"{self.base_url}/rpc/{function_name}"
        resp = httpx.post(url, headers=self.headers, json=params)
        resp.raise_for_status()
        return resp.json()

    def get(self, table: str, params: dict = None):
        """Direct table access via PostgREST."""
        url = f"{self.base_url}/{table}"
        resp = httpx.get(url, headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()
    

from .utils import range_to_dates

class SalesService:
    @staticmethod
    def get_overview(vendor_id, range, status, granularity):
        start, end = range_to_dates(range)
        
        # Call Supabase RPC function: get_vendor_revenue_series
        revenue = SupabaseRestClient().rpc("get_vendor_revenue_series", {
            "p_vendor_id": str(vendor_id),
            "p_start": start,
            "p_end": end,
            "p_granularity": granularity,
            "p_status": None if status == 'all' else status
        })
        
        # Call another RPC for order totals
        orders_meta = SupabaseRestClient().rpc("get_vendor_orders_summary", {
            "p_vendor_id": str(vendor_id),
            "p_start": start,
            "p_end": end,
            "p_status": None if status == 'all' else status
        })
        
        # Call another RPC for top category
        top_cat = SupabaseRestClient().rpc("get_vendor_top_category", {
            "p_vendor_id": str(vendor_id),
            "p_start": start,
            "p_end": end,
        })
        
        total_sales = sum(r["value"] for r in revenue)
        total_orders = orders_meta[0]["total_orders"] if orders_meta else 0
        
        return {
            "revenue_series": revenue,
            "total_orders": total_orders,
            "total_sales": total_sales,
            "avg_order_value": total_sales / total_orders if total_orders else 0,
            "top_category": top_cat[0]["category_name"] if top_cat else "N/A"
        }

class OrdersService:
    @staticmethod
    def get_report(vendor_id, range, status, shipping_type, sort, search):
        start, end = range_to_dates(range)
        
        # Use RPC for the full filtered + sorted list
        rows = SupabaseRestClient().rpc("get_vendor_orders_report", {
            "p_vendor_id": str(vendor_id),
            "p_start": start,
            "p_end": end,
            "p_status": None if status == 'all' else status,
            "p_shipping_type": None if shipping_type == 'all' else shipping_type,
            "p_sort": sort,
            "p_search": search or None
        })
        
        return {
            "total_orders": len(rows),
            "orders": rows
        }

class ProductsService:
    @staticmethod
    def get_report(vendor_id, range, sort, search):
        start, end = range_to_dates(range) if range != 'all' else (None, None)
        
        rows = SupabaseRestClient().rpc("get_vendor_products_report", {
            "p_vendor_id": str(vendor_id),
            "p_start": start,
            "p_end": end,
            "p_sort": sort,
            "p_search": search or None
        })
        
        return {
            "products": rows
        }