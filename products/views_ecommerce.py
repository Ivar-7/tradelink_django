from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Q
from drf_spectacular.utils import extend_schema
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from products.models import Product, Stock, InventoryMovement
from products.serializers import (
    ProductListSerializer,
    ProductSerializer,
    ProductCreateUpdateSerializer,
    StockSerializer,
    InventoryMovementSerializer
)


# ---------------------------
# PAGINATION
# ---------------------------

class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"
    max_page_size = 100


# ---------------------------
# FILTERS
# ---------------------------

class ProductFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    category_id = django_filters.UUIDFilter(field_name="category_id")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Product
        fields = []

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )


# ---------------------------
# PUBLIC PRODUCT BROWSING
# ---------------------------

class ProductBrowseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    PUBLIC: Browse products from verified vendors
    """

    permission_classes = [permissions.AllowAny]
    pagination_class = ProductPagination

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ProductFilter

    ordering_fields = ["created_at", "price", "average_rating"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Product.objects.filter(
                is_active=True,
                vendor__vendorprofile__is_verified=True,
                vendor__vendorprofile__is_suspended=False,
            )
            .select_related("vendor", "category")
            .prefetch_related("reviews")
        )

    def get_serializer_class(self):
        return ProductSerializer if self.action == "retrieve" else ProductListSerializer

    # ---------------------------
    # STOCK OPTIONS (MULTI-VENDOR)
    # ---------------------------

    @extend_schema(description="Get available stock options for a product")
    @action(detail=True, methods=["get"])
    def stock_options(self, request, pk=None):
        product = self.get_object()

        stocks = (
            Stock.objects.filter(
                product=product,
                vendor__vendorprofile__is_verified=True,
                vendor__vendorprofile__is_suspended=False,
                quantity__gt=0,
            )
            .select_related("vendor")
        )

        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)


# ---------------------------
# VENDOR PRODUCT MANAGEMENT
# ---------------------------

class VendorProductViewSet(viewsets.ModelViewSet):
    """
    PROTECTED: Vendor manages own products
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ProductPagination

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "price"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Product.objects.filter(vendor=self.request.user)
            .select_related("category")
        )

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProductCreateUpdateSerializer
        if self.action == "retrieve":
            return ProductSerializer
        return ProductListSerializer

    # ---------------------------
    # SAFE CREATE / UPDATE
    # ---------------------------

    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user)

    def perform_update(self, serializer):
        product = self.get_object()

        # 🔥 FIX: never return Response here (DRF ignores it)
        if product.vendor != self.request.user:
            raise PermissionError("You do not own this product")

        serializer.save()

    # ---------------------------
    # TOGGLE ACTIVE
    # ---------------------------

    @extend_schema(description="Toggle product active state")
    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        product = self.get_object()

        if product.vendor != request.user:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        product.is_active = not product.is_active
        product.save(update_fields=["is_active"])

        return Response({
            "message": "activated" if product.is_active else "deactivated",
            "is_active": product.is_active,
        })

    # ---------------------------
    # STOCK MANAGEMENT
    # ---------------------------

    @extend_schema(description="Get vendor stock for product")
    @action(detail=True, methods=["get"])
    def stock(self, request, pk=None):
        product = self.get_object()

        stocks = Stock.objects.filter(
            product=product,
            vendor=request.user
        )

        return Response(StockSerializer(stocks, many=True).data)

    @extend_schema(description="Create or update stock")
    @action(detail=True, methods=["post"])
    def update_stock(self, request, pk=None):
        product = self.get_object()

        if product.vendor != request.user:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        quantity = request.data.get("quantity")
        price = request.data.get("price")

        if quantity is None or price is None:
            return Response(
                {"error": "quantity and price required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stock, created = Stock.objects.get_or_create(
            product=product,
            vendor=request.user,
            defaults={
                "quantity": int(quantity),
                "price": price,
            },
        )

        if not created:
            stock.quantity = int(quantity)
            stock.price = price
            stock.save(update_fields=["quantity", "price"])

        return Response({
            "message": "created" if created else "updated",
            "stock": StockSerializer(stock).data,
        })

    # ---------------------------
    # INVENTORY AUDIT
    # ---------------------------

    @extend_schema(description="Inventory movement history")
    @action(detail=True, methods=["get"])
    def inventory_movements(self, request, pk=None):
        product = self.get_object()

        movements = (
            InventoryMovement.objects.filter(
                stock__product=product,
                stock__vendor=request.user,
            )
            .select_related("stock")
            .order_by("-created_at")
        )

        return Response(
            InventoryMovementSerializer(movements, many=True).data
        )