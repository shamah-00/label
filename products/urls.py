from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/industry/<str:industry_name>/', views.industry_products, name='industry_products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart, name='cart'),
    path('quote/', views.quote_cart, name='quote_cart'),
    path('shipping/', views.shipping, name='shipping'),
]
