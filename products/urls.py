from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter


from .views_ecommerce import ProductBrowseViewSet, VendorProductViewSet

router = DefaultRouter()
router.register(r'products/browse', ProductBrowseViewSet, basename='product-browse')
router.register(r'vendor/products', VendorProductViewSet, basename='vendor-product')

inventory_router = SimpleRouter()

urlpatterns = [
	path('', include(router.urls)),
]
