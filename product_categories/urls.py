# urls.py
from django.urls import path
from .views import ProductCategoryView

urlpatterns = [
    # List all categories or create a new one
    path('categories/', ProductCategoryView.as_view()),

    # Retrieve, update, patch, or delete a single category
    path('categories/<str:pk>/', ProductCategoryView.as_view()),
]