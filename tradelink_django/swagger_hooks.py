def organize_endpoint_tags(result, generator, request, public):
    """Group endpoints in Swagger by business area using predictable tag titles."""

    user_prefixes = (
        "/api/v1/auth/",
        "/api/v1/users/",
        "/api/v1/addresses",
        "/api/v1/products",
        "/api/v1/orders",
        "/api/v1/reviews",
        "/api/v1/payments",
        "/api/v1/carts",
        "/api/v1/feedback",
    )
    category_prefixes = ("/api/v1/categories",)
    admin_prefixes = (
        "/api/v1/admin/",
        "/api/v1/dashboard/",
    )
    vendor_prefixes = (
        "/api/v1/vendors",
        "/api/v1/store",
        "/api/v1/inventory",
        "/api/v1/payouts",
        "/api/v1/wallet",
        "/api/v1/reports",
        "/api/v1/settings",
        "/api/v1/notifications",
    )

    for path, operations in result.get("paths", {}).items():
        assigned_tag = None

        if path.startswith(category_prefixes):
            assigned_tag = "2. Categories & Catalog"
        elif path.startswith(admin_prefixes):
            assigned_tag = "3. Admin Dashboard Endpoints"
        elif path.startswith(vendor_prefixes):
            assigned_tag = "4. Vendor Endpoints"
        elif path.startswith(user_prefixes):
            assigned_tag = "1. User Website Endpoints"

        if not assigned_tag:
            continue

        for method, operation in operations.items():
            if method.lower() in {"get", "post", "put", "patch", "delete", "options", "head", "trace"}:
                operation["tags"] = [assigned_tag]

    return result