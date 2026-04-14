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
                "parent_id": item.get("parent_id"),
                "sort_order": item.get("sort_order", 0),
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
                "parent_id": category.get("parent_id"),
                "sort_order": category.get("sort_order", 0),
            }
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = ProductCategoryService.create_category(
            name=serializer.validated_data["name"],
            description=serializer.validated_data.get("description"),
            parent_id=serializer.validated_data.get("parent").id if serializer.validated_data.get("parent") else None,
            sort_order=serializer.validated_data.get("sort_order", 0),
        )
        return Response(
            {
                "id": category.get("category_id"),
                "name": category.get("name"),
                "description": category.get("description"),
                "image_url": category.get("image_url", ""),
                "parent_id": category.get("parent_id"),
                "sort_order": category.get("sort_order", 0),
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
            parent_id=serializer.validated_data.get("parent").id if serializer.validated_data.get("parent") else None,
            sort_order=serializer.validated_data.get("sort_order", 0),
        )
        if not category:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "id": category.get("category_id"),
                "name": category.get("name"),
                "description": category.get("description"),
                "image_url": category.get("image_url", ""),
                "parent_id": category.get("parent_id"),
                "sort_order": category.get("sort_order", 0),
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
                "parent_id": category.get("parent_id"),
                "sort_order": category.get("sort_order", 0),
            }
        )

    def destroy(self, request, pk=None, *args, **kwargs):
        if not ProductCategoryService.delete_category(pk):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        categories = ProductCategoryService.list_categories()
        by_id = {
            item.get('category_id'): {
                'id': item.get('category_id'),
                'name': item.get('name'),
                'description': item.get('description'),
                'parent_id': item.get('parent_id'),
                'sort_order': item.get('sort_order', 0),
                'children': [],
            }
            for item in categories
        }

        roots = []
        for node in by_id.values():
            parent_id = node.get('parent_id')
            if parent_id and parent_id in by_id:
                by_id[parent_id]['children'].append(node)
            else:
                roots.append(node)

        def sort_tree(nodes):
            nodes.sort(key=lambda n: (n.get('sort_order', 0), str(n.get('name') or '').lower()))
            for child in nodes:
                sort_tree(child['children'])

        sort_tree(roots)

        return Response(
            {
                'categories': roots
            }
        )
