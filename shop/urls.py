from django.urls import path, include, register_converter
from . import views, converters

app_name = 'shop'
register_converter(converters.NegativeIntConverter, 'negint')

products_patterns = [
    # products/
    # path('<int:category_id>',views.CategoryProductList.as_view(), name="category_products"),
    # path('favorites', views.FavoriteProductList.as_view(), name="favorite_products"),
    # path('search', views.search_products, name="search_products"),
    path('sale', views.SaleProductList.as_view(), name="sale_products"),
]

product_patterns = [
    # product/
    path('add/', views.ProductCreate.as_view(), name='product_add'),
    path('<int:pk>/', views.ProductDetail.as_view(), name="product_details"),
    path('<int:pk>/update/', views.ProductUpdate.as_view(), name="product_update"),
    path('<int:pk>/delete/', views.ProductDelete.as_view(), name="product_delete"),
    path('<int:product_id>/rate/', views.rate_product, name="rate_product"),
    path('<int:product_id>/question/', views.question_product, name="question_product"),
    path('<int:product_id>/favorite/', views.favorite, name="favorite"),
    path('<int:product_id>/unfavorite/', views.unfavorite, name="unfavorite"),
    path('product_photo/<int:product_photo_id>/delete/', views.product_photo_delete, name="product_photo_delete"),
    path('product_photo/<int:product_photo_id>/makeprimary/', views.product_photo_make_primary, name="product_photo_make_primary"),
]

promotion_patterns = [
    # promotion/
    path('add/', views.PromotionCreate.as_view(), name='promotion_add'),
    path('<int:pk>/', views.PromotionDetail.as_view(), name="promotion_details"),
    path('<int:pk>/update/', views.PromotionUpdate.as_view(), name="promotion_update"),
    path('<int:pk>/delete/', views.PromotionDelete.as_view(), name="promotion_delete"),
]

category_patterns = [
    # category/
    # path('', views.CategoryList.as_view(), name="categories"),
    path('add/', views.CategoryCreate.as_view(), name="category_add"),
    path('<int:pk>/', views.CategoryDetail.as_view(), name="category_details"),
    path('<int:pk>/update/', views.CategoryUpdate.as_view(), name="category_update"),
    path('<int:pk>/delete/', views.CategoryDelete.as_view(), name="category_delete"),
]

urlpatterns = [
    path('', views.ProductList.as_view(), name='index'), #views.index, name="index"),
    path('product/', include(product_patterns)),
    path('products/', include(products_patterns)),
    path('promotion/', include(promotion_patterns)),
    path('promotions/', views.PromotionList.as_view(), name="promotions"), # list of promotions
    path('category/', include(category_patterns)), # adding, deleting, updating, viewwing individual categories
    path('categories/', views.CategoryList.as_view(), name="categories"), # list of categories
    path('categories/<int:category_id>',views.CategoryProductList.as_view(), name="category_products"), # products related to categories
    path('favorites/', views.FavoriteProductList.as_view(), name="favorite_products"),
    path('rating/<int:rating_id>/vote/<negint:score>', views.rating_vote, name="rating_vote"),
]