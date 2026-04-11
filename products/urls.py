from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter

from .views import InventoryViewSet, ProductViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

inventory_router = SimpleRouter()
inventory_router.register(r'inventory', InventoryViewSet, basename='inventory')

urlpatterns = [
	path('', include(router.urls)),
	path('', include(inventory_router.urls)),
]
