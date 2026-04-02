from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .serializers import ProductCreateUpdateSerializer
from .services import ProductService


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
    permission_classes = [permissions.AllowAny]
    pagination_class = ProductPagination

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductCreateUpdateSerializer

    @staticmethod
    def _normalize(item):
        return {
            'id': item.get('product_id'),
            'name': item.get('product_name'),
            'price': item.get('price'),
            'description': item.get('product_description', ''),
            'stock_quantity': item.get('stock', 0),
            'image_url': item.get('image_url', ''),
            'category_id': item.get('category_id'),
            'vendor_id': item.get('vendor_id'),
            'vendor_name': item.get('vendor_name'),
            'average_rating': item.get('average_rating', 0),
            'review_count': item.get('review_count', 0),
            'created_at': item.get('created_at'),
        }

    def list(self, request, *args, **kwargs):
        """Override list to include pagination info."""
        filters = {
            'search': request.query_params.get('search'),
            'category_id': request.query_params.get('category_id'),
            'min_price': float(request.query_params.get('min_price')) if request.query_params.get('min_price') else None,
            'max_price': float(request.query_params.get('max_price')) if request.query_params.get('max_price') else None,
            'in_stock': request.query_params.get('in_stock', '').lower() == 'true',
        }
        products = [self._normalize(p) for p in ProductService.get_products(filters)]
        page = self.paginate_queryset(products)

        if page is not None:
            paginated_response = self.get_paginated_response(page)
            # Convert to match spec format
            return Response({
                'products': paginated_response.data['results'],
                'total': paginated_response.data['count'],
                'page': request.query_params.get('page', 1),
                'limit': request.query_params.get('limit', 20),
            })

        return Response({
            'products': products,
            'total': len(products),
            'page': 1,
            'limit': len(products),
        })

    def retrieve(self, request, pk=None, *args, **kwargs):
        product = ProductService.get_product(pk)
        if not product:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self._normalize(product))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = {
            'product_name': serializer.validated_data['name'],
            'price': float(serializer.validated_data['price']),
            'product_description': serializer.validated_data.get('description', ''),
            'stock': serializer.validated_data.get('stock_quantity', 0),
            'image_url': serializer.validated_data.get('image_url', ''),
            'category_id': str(serializer.validated_data['category'].id) if serializer.validated_data.get('category') else None,
        }
        created = ProductService.create_product(payload)
        return Response(self._normalize(created), status=status.HTTP_201_CREATED)

    def update(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = {
            'product_name': serializer.validated_data['name'],
            'price': float(serializer.validated_data['price']),
            'product_description': serializer.validated_data.get('description', ''),
            'stock': serializer.validated_data.get('stock_quantity', 0),
            'image_url': serializer.validated_data.get('image_url', ''),
            'category_id': str(serializer.validated_data['category'].id) if serializer.validated_data.get('category') else None,
        }
        updated = ProductService.update_product(pk, payload)
        if not updated:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self._normalize(updated))

    def partial_update(self, request, pk=None, *args, **kwargs):
        field_map = {
            'name': 'product_name',
            'price': 'price',
            'description': 'product_description',
            'stock_quantity': 'stock',
            'image_url': 'image_url',
            'category_id': 'category_id',
        }
        payload = {field_map[k]: v for k, v in request.data.items() if k in field_map}
        updated = ProductService.update_product(pk, payload)
        if not updated:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self._normalize(updated))

    def destroy(self, request, pk=None, *args, **kwargs):
        if not ProductService.delete_product(pk):
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """GET /products/search/ - Search products."""
        return self.list(request)

