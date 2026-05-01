from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # API schema & docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # v1 apps
    path('api/v1/', include('users.urls')),
    path('api/v1/', include('addresses.urls')),
    path('api/v1/', include('products.urls')),
    path('api/v1/', include('product_categories.urls')),
    path('api/v1/', include('orders.urls')),
    path('api/v1/', include('reviews.urls')),
    path('api/v1/', include('payments.urls')),
    path('api/v1/', include('carts.urls')),
    path('api/v1/', include('feedback.urls')),
]

