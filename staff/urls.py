from django.urls import path
from . import views

urlpatterns = [
    path("", views.staff_dashboard, name="staff_dashboard"),
    path("login/", views.staff_login, name="staff_login"),
    path("logout/", views.staff_logout, name="staff_logout"),
    path("register/", views.staff_register, name="staff_register"),
    path("register/success/", views.staff_registration_success, name="staff_registration_success"),
    path("profile/", views.staff_profile, name="staff_profile"),
    
    # Products
    path("products/", views.staff_products, name="staff_products"),
    path("products/", views.staff_products, name="staff_product_list"),
    path("products/add/", views.staff_product_add, name="staff_product_add"),
    path("products/<int:pk>/edit/", views.staff_product_edit, name="staff_product_edit"),
    
    # Customers
    path("customers/", views.staff_customers, name="staff_customers"),
    path("customers/", views.staff_customers, name="staff_customer_list"),
    
    # Orders
    path("orders/", views.staff_orders, name="staff_orders"),
    path("orders/<int:pk>/", views.staff_order_detail, name="staff_order_detail"),
    
    # Quotes
    path("quotes/", views.staff_quotes, name="staff_quotes"),
    path("quotes/", views.staff_quotes, name="staff_quote_list"),
    path("quotes/<int:pk>/", views.staff_quote_detail, name="staff_quote_detail"),
    
    # Calendar Orders
    path("calendar-orders/", views.staff_calendar_orders, name="staff_calendar_orders"),
    path("calendar-orders/<int:pk>/", views.staff_calendar_order_detail, name="staff_calendar_order_detail"),
    
    # Boss / Staff Management paths
    path("boss/staff/", views.boss_staff_management, name="boss_staff_management"),
    path("staff-management/", views.boss_staff_management),
    
    path("boss/staff/create/", views.owner_create_staff, name="owner_create_staff"),
    path("staff-management/create/", views.owner_create_staff),
    
    path("boss/staff/<int:pk>/approve/", views.approve_staff, name="approve_staff"),
    path("boss/staff/<int:pk>/reject/", views.reject_staff, name="reject_staff"),
    path("boss/staff/<int:pk>/deactivate/", views.deactivate_staff, name="deactivate_staff"),
    path("boss/staff/<int:pk>/reactivate/", views.reactivate_staff, name="reactivate_staff"),
    path("boss/staff/<int:pk>/remove/", views.remove_staff, name="remove_staff"),
    path("boss/activity/", views.staff_activity_log, name="staff_activity_log"),
]