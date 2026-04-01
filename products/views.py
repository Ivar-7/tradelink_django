from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from .models import Product
from .serializers import ProductSerializer, ProductListSerializer, ProductCreateUpdateSerializer


class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100


class ProductViewSet(viewsets.ModelViewSet):
    """
    API for managing products.
    
    Query params:
    - search: Search by name or description
    - category_id: Filter by category
    - min_price: Minimum price
    - max_price: Maximum price
    - in_stock: Filter to in-stock items only (true/false)
    - page: Page number
    - limit: Items per page (max 100)
    """
    queryset = Product.objects.all().order_by('-created_at')
    permission_classes = [permissions.AllowAny]
    pagination_class = ProductPagination

    def get_serializer_class(self):
        if self.action in ['list']:
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def get_queryset(self):
        """Apply filters from query params."""
        queryset = super().get_queryset()

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        # Category
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Price range
        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=float(min_price))

        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=float(max_price))

        # In stock
        in_stock = self.request.query_params.get('in_stock')
        if in_stock and in_stock.lower() == 'true':
            queryset = queryset.filter(stock_quantity__gt=0)

        return queryset

    def list(self, request, *args, **kwargs):
        """Override list to include pagination info."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            # Convert to match spec format
            return Response({
                'products': paginated_response.data['results'],
                'total': paginated_response.data['count'],
                'page': request.query_params.get('page', 1),
                'limit': request.query_params.get('limit', 20),
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'products': serializer.data,
            'total': len(serializer.data),
            'page': 1,
            'limit': len(serializer.data),
        })

    @action(detail=False, methods=['get'])
    def search(self, request):
        """GET /products/search/ - Search products."""
        return self.list(request)

