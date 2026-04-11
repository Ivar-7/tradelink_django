from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import ProductCategorySerializer
from .services import ProductCategoryService


class ProductCategoryViewSet(viewsets.ModelViewSet):
    """
    API for product categories.
    """
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        categories = ProductCategoryService.list_categories()
        normalized = [
            {
                "id": item.get("category_id"),
                "name": item.get("name"),
                "description": item.get("description"),
                "image_url": item.get("image_url", ""),
            }
            for item in categories
        ]
        return Response(normalized)

    def retrieve(self, request, pk=None, *args, **kwargs):
        category = ProductCategoryService.get_category(pk)
        if not category:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "id": category.get("category_id"),
                "name": category.get("name"),
                "description": category.get("description"),
                "image_url": category.get("image_url", ""),
            }
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = ProductCategoryService.create_category(
            name=serializer.validated_data["name"],
            description=serializer.validated_data.get("description"),
        )
        return Response(
            {
                "id": category.get("category_id"),
                "name": category.get("name"),
                "description": category.get("description"),
                "image_url": category.get("image_url", ""),
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = ProductCategoryService.update_category(
            category_id=pk,
            name=serializer.validated_data["name"],
            description=serializer.validated_data.get("description"),
        )
        if not category:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "id": category.get("category_id"),
                "name": category.get("name"),
                "description": category.get("description"),
                "image_url": category.get("image_url", ""),
            }
        )

    def partial_update(self, request, pk=None, *args, **kwargs):
        category = ProductCategoryService.partial_update_category(pk, request.data)
        if not category:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "id": category.get("category_id"),
                "name": category.get("name"),
                "description": category.get("description"),
                "image_url": category.get("image_url", ""),
            }
        )

    def destroy(self, request, pk=None, *args, **kwargs):
        if not ProductCategoryService.delete_category(pk):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        categories = ProductCategoryService.list_categories()
        return Response(
            {
                'categories': [
                    {
                        'id': item.get('category_id'),
                        'name': item.get('name'),
                        'description': item.get('description'),
                        'children': [],
                    }
                    for item in categories
                ]
            }
        )
