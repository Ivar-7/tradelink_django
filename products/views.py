from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .serializers import ProductCreateUpdateSerializer
from .services import ProductService


PRODUCT_IMAGES = {}


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
    def _to_smallint_price(value):
        # Supabase product.price is configured as integer-like in current schema.
        return int(float(value or 0))

    @staticmethod
    def _normalize(item):
        product_id = item.get('product_id')
        return {
            'id': product_id,
            'name': item.get('product_name'),
            'price': item.get('price'),
            'description': item.get('product_description', ''),
            'stock_quantity': item.get('stock', 0),
            'image_url': item.get('image_url', ''),
            'status': item.get('status', 'draft'),
            'images': PRODUCT_IMAGES.get(str(product_id), []),
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
            'price': self._to_smallint_price(serializer.validated_data['price']),
            'product_description': serializer.validated_data.get('description', ''),
            'stock': serializer.validated_data.get('stock_quantity', 0),
            'image_url': serializer.validated_data.get('image_url', ''),
            'category_id': str(serializer.validated_data.get('category_id')) if serializer.validated_data.get('category_id') else None,
        }
        created = ProductService.create_product(payload)
        return Response(self._normalize(created), status=status.HTTP_201_CREATED)

    def update(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = {
            'product_name': serializer.validated_data['name'],
            'price': self._to_smallint_price(serializer.validated_data['price']),
            'product_description': serializer.validated_data.get('description', ''),
            'stock': serializer.validated_data.get('stock_quantity', 0),
            'image_url': serializer.validated_data.get('image_url', ''),
            'category_id': str(serializer.validated_data.get('category_id')) if serializer.validated_data.get('category_id') else None,
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
        if 'price' in payload:
            payload['price'] = self._to_smallint_price(payload['price'])
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

    @action(detail=True, methods=['patch'], url_path='publish')
    def publish(self, request, pk=None):
        product = ProductService.update_product(pk, {'status': 'published'})
        if not product:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self._normalize(product))

    @action(detail=True, methods=['patch'], url_path='archive')
    def archive(self, request, pk=None):
        product = ProductService.update_product(pk, {'status': 'archived'})
        if not product:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self._normalize(product))

    @action(detail=False, methods=['post'], url_path='bulk-upload')
    def bulk_upload(self, request):
        products = request.data.get('products', [])
        created = []
        for item in products:
            payload = {
                'product_name': item.get('name', ''),
                'price': self._to_smallint_price(item.get('price', 0) or 0),
                'product_description': item.get('description', ''),
                'stock': int(item.get('stock_quantity', 0) or 0),
                'image_url': item.get('image_url', ''),
                'category_id': item.get('category_id'),
            }
            created_item = ProductService.create_product(payload)
            if created_item:
                created.append(self._normalize(created_item))
        return Response({'created': created, 'count': len(created)}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch'], url_path='bulk-update')
    def bulk_update(self, request):
        updates = request.data.get('products', [])
        updated_items = []
        field_map = {
            'name': 'product_name',
            'price': 'price',
            'description': 'product_description',
            'stock_quantity': 'stock',
            'image_url': 'image_url',
            'category_id': 'category_id',
            'status': 'status',
        }
        for item in updates:
            product_id = item.get('id')
            if not product_id:
                continue
            payload = {field_map[k]: v for k, v in item.items() if k in field_map}
            if 'price' in payload:
                payload['price'] = self._to_smallint_price(payload['price'])
            updated = ProductService.update_product(product_id, payload)
            if updated:
                updated_items.append(self._normalize(updated))
        return Response({'updated': updated_items, 'count': len(updated_items)})

    @action(detail=True, methods=['post'], url_path='images')
    def add_image(self, request, pk=None):
        product = ProductService.get_product(pk)
        if not product:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        image_url = request.data.get('image_url')
        if not image_url:
            return Response({'detail': 'image_url is required.'}, status=status.HTTP_400_BAD_REQUEST)
        import uuid

        image_obj = {'id': str(uuid.uuid4()), 'image_url': image_url}
        key = str(pk)
        PRODUCT_IMAGES.setdefault(key, []).append(image_obj)
        return Response(image_obj, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'images/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        key = str(pk)
        images = PRODUCT_IMAGES.get(key, [])
        for image in images:
            if str(image.get('id')) == str(image_id):
                images.remove(image)
                PRODUCT_IMAGES[key] = images
                return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Image not found.'}, status=status.HTTP_404_NOT_FOUND)


class InventoryViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        products = ProductService.get_products({})
        inventory = [
            {
                'product_id': p.get('product_id'),
                'name': p.get('product_name'),
                'stock_quantity': int(p.get('stock') or 0),
                'status': 'low' if int(p.get('stock') or 0) <= 5 else 'ok',
            }
            for p in products
        ]
        return Response({'inventory': inventory, 'total': len(inventory)})

    def partial_update(self, request, pk=None):
        stock_quantity = request.data.get('stock_quantity')
        if stock_quantity is None:
            return Response({'detail': 'stock_quantity is required.'}, status=status.HTTP_400_BAD_REQUEST)
        updated = ProductService.update_product(pk, {'stock': int(stock_quantity)})
        if not updated:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                'product_id': updated.get('product_id'),
                'stock_quantity': int(updated.get('stock') or 0),
            }
        )

    @action(detail=False, methods=['get'], url_path='low-stock')
    def low_stock(self, request):
        threshold = int(request.query_params.get('threshold', 5))
        products = ProductService.get_products({})
        low = [
            {
                'product_id': p.get('product_id'),
                'name': p.get('product_name'),
                'stock_quantity': int(p.get('stock') or 0),
            }
            for p in products
            if int(p.get('stock') or 0) <= threshold
        ]
        return Response({'items': low, 'total': len(low), 'threshold': threshold})

