from django.urls import include, path
from rest_framework.routers import DefaultRouter


from .views_ecommerce import (
    AdminOrderViewSet,
    CartViewSet,
    OrderViewSet,
    ProductBrowseViewSet,
    ShipmentTrackingViewSet,
    VendorDashboardViewSet,
)

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'vendor/dashboard', VendorDashboardViewSet, basename='vendor-dashboard')
router.register(r'products/browse', ProductBrowseViewSet, basename='product-browse')
router.register(r'admin/orders', AdminOrderViewSet, basename='admin-orders')
router.register(r'shipments', ShipmentTrackingViewSet, basename='shipment-tracking')

urlpatterns = [
    path('', include(router.urls)),
]

