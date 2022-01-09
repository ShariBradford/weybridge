from django.urls import path, include, register_converter
from . import views

app_name = 'cart'

urlpatterns = [
    # cart/
    path('', views.view_cart, name="cart_details"), # views.CategoryDetail.as_view(), name="category_details"),
    path('<int:product_id>/', views.add_to_cart, name="add_to_cart"), # views.CategoryCreate.as_view(), name="category_add"),
    path('<int:product_id>/remove/', views.remove_from_cart, name="remove_from_cart"),
    path('<int:product_id>/update/', views.update_cart, name="update_cart"),
    # path('<int:pk>/delete/', views.CategoryDelete.as_view(), name="category_delete"),
    path('test/', views.test_cart, name="test_cart"),
    path('test/<int:new_cart_id>/', views.test_cart, name="test_cart"),
    path('clear-id/', views.clear_cart_id_from_session, name="clear_cart_id"),
    path('revive/', views.revive_cart, name="revive_cart"),
    path('get-id/', views.get_cart_id, name="get_cart_id"),
]