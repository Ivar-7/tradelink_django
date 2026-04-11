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
from .marketplace_views import (
    AdminVendorsView,
    AdminVendorStatusView,
    CustomReportView,
    DashboardSummaryView,
    ExportReportView,
    NotificationsView,
    NotificationReadView,
    OrdersReportView,
    PayoutDetailView,
    PayoutsView,
    ProductsReportView,
    RevenueReportView,
    SettingsView,
    StoreView,
    VendorApplicationView,
    VendorApplyView,
    VendorProfileView,
    WalletView,
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

    # Vendor admission and profile
    path('vendors/apply', VendorApplyView.as_view(), name='vendor-apply'),
    path('vendors/application', VendorApplicationView.as_view(), name='vendor-application'),
    path('admin/vendors', AdminVendorsView.as_view(), name='admin-vendors'),
    path('admin/vendors/<str:user_id>/status', AdminVendorStatusView.as_view(), name='admin-vendor-status'),
    path('vendors/me', VendorProfileView.as_view(), name='vendor-me'),
    path('store', StoreView.as_view(), name='store'),

    # Settings and notifications
    path('settings', SettingsView.as_view(), name='settings'),
    path('notifications', NotificationsView.as_view(), name='notifications'),
    path('notifications/<str:notification_id>/read', NotificationReadView.as_view(), name='notification-read'),

    # Payouts and wallet
    path('payouts', PayoutsView.as_view(), name='payouts'),
    path('payouts/<str:payout_id>', PayoutDetailView.as_view(), name='payout-detail'),
    path('wallet', WalletView.as_view(), name='wallet'),

    # Reports and dashboard summary
    path('reports/revenue', RevenueReportView.as_view(), name='report-revenue'),
    path('reports/orders', OrdersReportView.as_view(), name='report-orders'),
    path('reports/products', ProductsReportView.as_view(), name='report-products'),
    path('reports/custom', CustomReportView.as_view(), name='report-custom'),
    path('reports/export', ExportReportView.as_view(), name='report-export'),
    path('dashboard/summary', DashboardSummaryView.as_view(), name='dashboard-summary'),
]

