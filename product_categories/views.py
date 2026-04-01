from rest_framework import viewsets, permissions
from .models import ProductCategory
from .serializers import ProductCategorySerializer


class ProductCategoryViewSet(viewsets.ModelViewSet):
    """
    API for product categories.
    """
    queryset = ProductCategory.objects.all().order_by('name')
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.AllowAny]
