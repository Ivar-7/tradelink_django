from django.urls import path

from .views import (
    cart_list, cart_add_item, cart_update_item, 
    cart_delete_item, cart_clear
)

urlpatterns = [
    path('cart/', cart_list, name='cart-list'),
    path('cart/items/', cart_add_item, name='cart-add-item'),
    path('cart/items/<str:item_id>/', cart_update_item, name='cart-update-item'),
    path('cart/items/<str:item_id>/delete/', cart_delete_item, name='cart-delete-item'),
    path('cart/clear/', cart_clear, name='cart-clear'),
]


