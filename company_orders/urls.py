from django.urls import path
from . import views

app_name = "company_orders"

urlpatterns = [
    path("", views.company_order, name="order"),
    path("submitted/", views.company_order_success, name="success"),
]
