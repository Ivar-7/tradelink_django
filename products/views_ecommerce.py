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
    ProductListSerializer, ProductSerializer, ProductCreateUpdateSerializer,
    StockSerializer, InventoryMovementSerializer
)


class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100


class ProductFilter(django_filters.FilterSet):
    """Filters for product browsing."""
    search = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Search by name'
    )
    category_id = django_filters.UUIDFilter(
        field_name='category_id',
        label='Filter by category'
    )
    min_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        label='Minimum price'
    )
    max_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        label='Maximum price'
    )
    
    class Meta:
        model = Product
        fields = []


class ProductBrowseViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse products from verified vendors - PUBLIC endpoint."""
    permission_classes = [permissions.AllowAny]
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'price', 'average_rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Only show active products from verified, non-suspended vendors."""
        return Product.objects.filter(
            is_active=True,
            vendor__vendorprofile__is_verified=True,
            vendor__vendorprofile__is_suspended=False
        ).select_related('vendor', 'category').prefetch_related('reviews')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductSerializer
        return ProductListSerializer
    
    @extend_schema(description="Get available stock for product")
    @action(detail=True, methods=['get'])
    def stock_options(self, request, pk=None):
        """Get available stock entries for this product (from different vendors)."""
        try:
            product = Product.objects.get(id=pk)
            stocks = Stock.objects.filter(
                product=product,
                vendor__vendorprofile__is_verified=True,
                vendor__vendorprofile__is_suspended=False,
                quantity__gt=0
            ).select_related('vendor')
            
            serializer = StockSerializer(stocks, many=True)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class VendorProductViewSet(viewsets.ModelViewSet):
    """Manage vendor's own products - PROTECTED endpoint."""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ProductPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get products for current vendor only."""
        return Product.objects.filter(vendor=self.request.user).select_related('category')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        if self.action == 'retrieve':
            return ProductSerializer
        return ProductListSerializer
    
    def perform_create(self, serializer):
        """Create product for current vendor."""
        serializer.save(vendor=self.request.user)
    
    def perform_update(self, serializer):
        """Update vendor's product."""
        product = self.get_object()
        if product.vendor != self.request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()
    
    @extend_schema(description="Toggle product active/inactive status")
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle product active status."""
        try:
            product = self.get_object()
            if product.vendor != request.user:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            product.is_active = not product.is_active
            product.save()
            
            return Response({
                'message': f"Product {'activated' if product.is_active else 'deactivated'}",
                'is_active': product.is_active
            })
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(description="Get stock for vendor's product")
    @action(detail=True, methods=['get'])
    def stock(self, request, pk=None):
        """Get stock entries for vendor's product."""
        try:
            product = self.get_object()
            stocks = Stock.objects.filter(
                product=product,
                vendor=request.user
            )
            
            serializer = StockSerializer(stocks, many=True)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(description="Manage stock inventory")
    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """Update or create stock for product."""
        try:
            product = self.get_object()
            if product.vendor != request.user:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            quantity = request.data.get('quantity')
            price = request.data.get('price')
            
            if quantity is None or price is None:
                return Response(
                    {'error': 'quantity and price are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            stock, created = Stock.objects.get_or_create(
                product=product,
                vendor=request.user,
                defaults={'quantity': int(quantity), 'price': price}
            )
            
            if not created:
                stock.quantity = int(quantity)
                stock.price = price
                stock.save()
            
            serializer = StockSerializer(stock)
            return Response({
                'message': f"Stock {'created' if created else 'updated'}",
                'stock': serializer.data
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(description="Get inventory movement audit trail")
    @action(detail=True, methods=['get'])
    def inventory_movements(self, request, pk=None):
        """Get inventory movement history for vendor's product."""
        try:
            product = self.get_object()
            movements = InventoryMovement.objects.filter(
                stock__product=product,
                stock__vendor=request.user
            ).order_by('-created_at')
            
            serializer = InventoryMovementSerializer(movements, many=True)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
