from django.urls import path
from . import views

urlpatterns = [
    path("shipping/", views.staff_shipping_dashboard, name="staff_shipping_dashboard"),
    path("", views.staff_dashboard, name="staff_dashboard"),
    path("login/", views.staff_login, name="staff_login"),
    path("logout/", views.staff_logout, name="staff_logout"),
    path("profile/", views.staff_profile, name="staff_profile"),
    
    # Products
    path("products/", views.staff_products, name="staff_products"),
    path("products/add/", views.staff_product_add, name="staff_product_add"),
    path("products/<int:pk>/edit/", views.staff_product_edit, name="staff_product_edit"),
    path("products/<int:pk>/image/delete/", views.staff_product_image_delete, name="staff_product_image_delete"),
    
    # Customers
    path("customers/", views.staff_customers, name="staff_customers"),
    
    # Orders
    path("orders/", views.staff_orders, name="staff_orders"),
    path("orders/<int:pk>/delete/", views.boss_delete_order, name="boss_delete_order"),
    path("orders/<int:pk>/", views.staff_order_detail, name="staff_order_detail"),
    path("invoices/<int:pk>/", views.staff_invoice_detail, name="staff_invoice_detail"),
    
    # Quotes
    path("quotes/", views.staff_quotes, name="staff_quotes"),
    path("quotes/<int:pk>/", views.staff_quote_detail, name="staff_quote_detail"),
    
    # Calendar Orders
    path("calendar-orders/", views.staff_calendar_orders, name="staff_calendar_orders"),
    path("calendar-orders/<int:pk>/", views.staff_calendar_order_detail, name="staff_calendar_order_detail"),
    
    # Boss / Staff Management paths
    
    
    path("staff-management/", views.boss_staff_management, name="boss_staff_management"),
    path("boss/activity/", views.staff_activity_log, name="staff_activity_log"),
    path("boss/site-settings/", views.boss_site_settings, name="boss_site_settings"),
    path("boss/payment-settings/", views.boss_payment_settings, name="boss_payment_settings"),
]
