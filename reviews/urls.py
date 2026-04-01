from django.urls import include, path
from rest_framework.routers import SimpleRouter
from .views import ProductReviewViewSet

router = SimpleRouter()
router.register(r'reviews', ProductReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]

