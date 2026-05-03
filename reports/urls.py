from django.urls import path
from . import views

urlpatterns = [
    # Core
    path('sales/', views.SalesReportView.as_view(), name='sales-report'),
    path('suborders/', views.SubordersReportView.as_view(), name='suborders-report'),
    
    # Inventory
    path('inventory/', views.InventoryReportView.as_view(), name='inventory-report'),
    path('movements/', views.MovementsReportView.as_view(), name='movements-report'),
    
    # Operations
    path('orders/', views.OrdersReportView.as_view(), name='orders-report'),
    path('shipments/', views.ShipmentsReportView.as_view(), name='shipments-report'),
    
    # Finance
    path('earnings/', views.EarningsReportView.as_view(), name='earnings-report'),
    path('payouts/', views.PayoutsReportView.as_view(), name='payouts-report'),
    
    # Product
    path('products/', views.ProductsReportView.as_view(), name='products-report'),
    path('reviews/', views.ReviewsReportView.as_view(), name='reviews-report'),
]