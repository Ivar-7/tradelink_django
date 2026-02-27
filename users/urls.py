from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AdminUserViewSet,
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
)

router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-users')

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),

    # User profile
    path('users/me/', MeView.as_view(), name='user-me'),
    path('users/me/change-password/', ChangePasswordView.as_view(), name='user-change-password'),

    # Admin
    path('', include(router.urls)),
]

