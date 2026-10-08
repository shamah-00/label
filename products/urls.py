from django.urls import path
from . import views

urlpatterns = [
    path("shipping/quote/", views.shipping_quote, name="shipping_quote"),

    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/industry/<str:industry_name>/', views.industry_products, name='industry_products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart, name='cart'),
    path('quote/', views.quote_cart, name='quote_cart'),
    path('quote/add/<int:product_id>/', views.add_to_quote, name='add_to_quote'),
    path('quote/remove/<int:product_id>/', views.remove_from_quote, name='remove_from_quote'),
    path('custom-orders/', views.custom_order, name='custom_order'),
    path('shipping/', views.shipping, name='shipping'),
]



