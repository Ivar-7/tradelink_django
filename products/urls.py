from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.views_ecommerce import VendorProductViewSet

from .views import ProductViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='products')
router.register(r'vendor/products', VendorProductViewSet, basename='vendor-products')

urlpatterns = [
	path('', include(router.urls)),
]
