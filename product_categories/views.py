import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .services import ProductCategoryService  # Import your service

logger = logging.getLogger(__name__)


class ProductCategoryView(APIView):
    """View for handling CRUD operations for product categories via Supabase."""

    permission_classes = [AllowAny]

    def get(self,  pk=None):
        """Get a single category if pk provided, otherwise list all categories."""
        try:
            if pk:
                category = ProductCategoryService.get_category(pk)
                if not category:
                    return Response({'detail': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
                return Response(category)
            else:
                categories = ProductCategoryService.list_categories()
                return Response(categories)
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Create a new category."""
        name = request.data.get('name')
        description = request.data.get('description')
        if not name:
            return Response({'detail': 'Name is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            category = ProductCategoryService.create_category(name=name, description=description)
            return Response(category, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating category: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        """Full update (PUT) of a category."""
        name = request.data.get('name')
        description = request.data.get('description')
        if not name:
            return Response({'detail': 'Name is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            category = ProductCategoryService.update_category(pk, name=name, description=description)
            return Response(category)
        except Exception as e:
            logger.error(f"Error updating category: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        """Partial update (PATCH) of a category."""
        data = {}
        if 'name' in request.data:
            data['name'] = request.data['name']
        if 'description' in request.data:
            data['description'] = request.data['description']
        if not data:
            return Response({'detail': 'No data provided for update.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            category = ProductCategoryService.partial_update_category(pk, data)
            return Response(category)
        except Exception as e:
            logger.error(f"Error patching category: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        """Delete a category."""
        try:
            success = ProductCategoryService.delete_category(pk)
            if success:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'detail': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting category: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)