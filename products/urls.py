from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
router.register(r'v1/products', ProductViewSet, basename='product')

urlpatterns = router.urls
