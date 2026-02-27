from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('addresses.urls')),
    path('api/', include('products.urls')),
    path('api/', include('orders.urls')),
    path('api/', include('reviews.urls')),
    path('api/', include('payments.urls')),
    path('api/', include('carts.urls')),
    path('api/', include('feedback.urls')),
]
