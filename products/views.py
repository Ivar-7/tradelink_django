from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .serializers import ProductSerializer
from .serializers import (
    ProductCreateUpdateSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
)
from .services import ProductService
import uuid

# Temporary in-memory image store
PRODUCT_IMAGES = {}


class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"
    max_page_size = 100


class ProductViewSet(viewsets.ModelViewSet):
    """
    Product API

    Supports:
    - Filtering
    - Pagination
    - Bulk operations
    - Status transitions
    """

    permission_classes = [permissions.AllowAny]
    pagination_class = ProductPagination

    # 🔥 Correct serializer resolution
    def get_serializer_class(self):  # type: ignore
        if self.action == "list":
            return ProductListSerializer
        elif self.action == "retrieve":
            return ProductDetailSerializer
        return ProductCreateUpdateSerializer

    # 🔥 Core data transformation (DB → API)
    @staticmethod
    def _normalize(item):
        if not item:
            return None

        product_id = item.get("product_id")

        return {
            "id": product_id,
            "name": item.get("product_name"),
            "price": item.get("price"),
            "description": item.get("product_description") or "",
            "stock_quantity": int(item.get("stock") or 0),
            "image_url": item.get("image_url") or "",
            "status": item.get("status", "draft"),
            "images": PRODUCT_IMAGES.get(str(product_id), []),
            "category_id": item.get("category_id"),
            "vendor_id": item.get("vendor_id"),
            "vendor_name": item.get("vendor_name"),
            "average_rating": float(item.get("average_rating") or 0),
            "review_count": int(item.get("review_count") or 0),
            "created_at": item.get("created_at"),
        }

    ## 🔥 API → DB payload mapping
    def _build_payload(self, validated_data):
        return {
            "product_name": validated_data["name"],
            "price": self._to_smallint_price(validated_data["price"]),
            "product_description": validated_data.get("description", ""),
            "stock": validated_data.get("stock_quantity", 0),
            "image_url": validated_data.get("image_url", ""),
            "category_id": str(validated_data.get("category_id")),
            "vendor_id": (
                str(validated_data.get("vendor_id"))
                if validated_data.get("vendor_id")
                else None
            ),
        }

    @staticmethod
    def _to_smallint_price(value):
        return int(float(value or 0))

    # ---------------------------
    # CRUD OPERATIONS
    # ---------------------------

    def list(self, request, *args, **kwargs):
        filters = {
            "search": request.query_params.get("search"),
            "category_id": request.query_params.get("category_id"),
            "min_price": (
                float(request.query_params.get("min_price"))
                if request.query_params.get("min_price")
                else None
            ),
            "max_price": (
                float(request.query_params.get("max_price"))
                if request.query_params.get("max_price")
                else None
            ),
            "in_stock": request.query_params.get("in_stock", "").lower() == "true",
        }

        products = [self._normalize(p) for p in ProductService.get_products(filters)]

        page = self.paginate_queryset(products)
        if page is not None:
            return Response(
                {
                    "products": page,
                    "total": self.paginator.page.paginator.count,
                    "page": int(request.query_params.get("page", 1)),
                    "limit": int(request.query_params.get("limit", 20)),
                }
            )

        return Response(
            {
                "products": products,
                "total": len(products),
                "page": 1,
                "limit": len(products),
            }
        )

    def retrieve(self, request, pk=None, *args, **kwargs):
        product = ProductService.get_product(pk)

        if not product:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(self._normalize(product))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = self._build_payload(serializer.validated_data)
        created = ProductService.create_product(payload)

        return Response(
            self._normalize(created),
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = self._build_payload(serializer.validated_data)
        updated = ProductService.update_product(pk, payload)

        if not updated:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(self._normalize(updated))

    def partial_update(self, request, pk=None, *args, **kwargs):
        field_map = {
            "name": "product_name",
            "price": "price",
            "description": "product_description",
            "stock_quantity": "stock",
            "image_url": "image_url",
            "category_id": "category_id",
            "status": "status",
        }

        payload = {}

        for key, value in request.data.items():
            if key in field_map:
                mapped_key = field_map[key]
                if key == "price":
                    value = self._to_smallint_price(value)
                payload[mapped_key] = value

        if not payload:
            return Response(
                {"detail": "No valid fields provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = ProductService.update_product(pk, payload)

        if not updated:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(self._normalize(updated))

    def destroy(self, request, pk=None, *args, **kwargs):
        deleted = ProductService.delete_product(pk)

        if not deleted:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    # ---------------------------
    # CUSTOM ACTIONS
    # ---------------------------

    @action(detail=False, methods=["get"])
    def search(self, request):
        return self.list(request)

    @action(detail=True, methods=["patch"])
    def publish(self, request, pk=None):
        return self._update_status(pk, "published")

    @action(detail=True, methods=["patch"])
    def archive(self, request, pk=None):
        return self._update_status(pk, "archived")

    def _update_status(self, pk, status_value):
        updated = ProductService.update_product(pk, {"status": status_value})

        if not updated:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(self._normalize(updated))

    # ---------------------------
    # BULK OPERATIONS
    # ---------------------------

    @action(detail=False, methods=["post"])
    def bulk_upload(self, request):
        items = request.data.get("products", [])
        created = []

        for item in items:
            payload = {
                "product_name": item.get("name", ""),
                "price": self._to_smallint_price(item.get("price", 0)),
                "product_description": item.get("description", ""),
                "stock": int(item.get("stock_quantity", 0)),
                "image_url": item.get("image_url", ""),
                "category_id": item.get("category_id"),
                "vendor_id": item.get("vendor_id"),
            }

            result = ProductService.create_product(payload)
            if result:
                created.append(self._normalize(result))

        return Response(
            {"created": created, "count": len(created)},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["patch"])
    def bulk_update(self, request):
        items = request.data.get("products", [])
        updated_items = []

        for item in items:
            product_id = item.get("id")
            if not product_id:
                continue

            payload = {}

            if "price" in item:
                payload["price"] = self._to_smallint_price(item["price"])

            for key in [
                "name",
                "description",
                "stock_quantity",
                "image_url",
                "category_id",
                "status",
            ]:
                if key in item:
                    mapped = {
                        "name": "product_name",
                        "description": "product_description",
                        "stock_quantity": "stock",
                    }.get(key, key)

                    payload[mapped] = item[key]

            updated = ProductService.update_product(product_id, payload)

            if updated:
                updated_items.append(self._normalize(updated))

        return Response({"updated": updated_items, "count": len(updated_items)})

    # ---------------------------
    # IMAGE MANAGEMENT
    # ---------------------------

    @action(detail=True, methods=["post"])
    def images(self, request, pk=None):
        product = ProductService.get_product(pk)

        if not product:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        image_url = request.data.get("image_url")

        if not image_url:
            return Response(
                {"detail": "image_url is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_obj = {"id": str(uuid.uuid4()), "image_url": image_url}

        PRODUCT_IMAGES.setdefault(str(pk), []).append(image_obj)

        return Response(image_obj, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"images/(?P<image_id>[^/.]+)")
    def delete_image(self, request, pk=None, image_id=None):
        images = PRODUCT_IMAGES.get(str(pk), [])

        for img in images:
            if img["id"] == image_id:
                images.remove(img)
                return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"detail": "Image not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


# ---------------------------
# INVENTORY VIEW
# ---------------------------


class InventoryViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        products = ProductService.get_products({})

        inventory = [
            {
                "product_id": p.get("product_id"),
                "name": p.get("product_name"),
                "stock_quantity": int(p.get("stock") or 0),
                "status": "low" if int(p.get("stock") or 0) <= 5 else "ok",
            }
            for p in products
        ]

        return Response({"inventory": inventory, "total": len(inventory)})

    def partial_update(self, request, pk=None):
        stock_quantity = request.data.get("stock_quantity")

        if stock_quantity is None:
            return Response(
                {"detail": "stock_quantity is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = ProductService.update_product(pk, {"stock": int(stock_quantity)})

        if not updated:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "product_id": updated.get("product_id"),
                "stock_quantity": int(updated.get("stock") or 0),
            }
        )

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        threshold = int(request.query_params.get("threshold", 5))

        products = ProductService.get_products({})

        low = [
            {
                "product_id": p.get("product_id"),
                "name": p.get("product_name"),
                "stock_quantity": int(p.get("stock") or 0),
            }
            for p in products
            if int(p.get("stock") or 0) <= threshold
        ]

        return Response({"items": low, "total": len(low), "threshold": threshold})
