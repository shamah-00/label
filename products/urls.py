from django.urls import path
from . import views

urlpatterns = [
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path("shipping/quote/", views.shipping_quote, name="shipping_quote"),

    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/industry/<str:industry_name>/', views.industry_products, name='industry_products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path("checkout/", views.checkout, name="checkout"),
    path("order-success/<int:order_id>/", views.order_success, name="order_success"),
    path('cart/', views.cart, name='cart'),
    path('quote/', views.quote_cart, name='quote_cart'),
    path('quote/add/<int:product_id>/', views.add_to_quote, name='add_to_quote'),
    path('quote/remove/<int:product_id>/', views.remove_from_quote, name='remove_from_quote'),
    path('custom-orders/', views.custom_order, name='custom_order'),
    path('shipping/', views.shipping, name='shipping'),
    path("invoice-payment/", views.invoice_payment, name="invoice_payment"),
]



