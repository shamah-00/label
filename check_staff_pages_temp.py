from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Order

User = get_user_model()
user = User.objects.filter(is_superuser=True, is_active=True).first()
client = Client(HTTP_HOST="localhost")

if user:
    client.force_login(user)
    print("Logged in as:", user.username)
else:
    print("WARNING: No active superuser found.")

checks = [
    ("Staff products", "/staff/products/"),
    ("Add product", "/staff/products/add/"),
    ("Staff orders", reverse("staff_orders")),
    ("Staff quotes", "/staff/quotes/"),
    ("Staff management", "/staff/boss/staff/"),
    ("Activity log", "/staff/boss/activity/"),
]

for label, url in checks:
    try:
        response = client.get(url)
        print(f"{label}: HTTP {response.status_code} | {url}")
    except Exception as exc:
        print(f"{label}: ERROR | {type(exc).__name__}: {exc}")

print("\nORDER DETAILS URL")
order = Order.objects.order_by("pk").first()

if order:
    try:
        url = reverse("staff_order_detail", args=[order.pk])
        response = client.get(url)
        print("URL:", url)
        print("HTTP status:", response.status_code)
    except Exception as exc:
        print(f"ERROR | {type(exc).__name__}: {exc}")
else:
    print("No orders exist in the database yet.")

print("\nFINAL DJANGO CHECK")
