from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.filter(is_superuser=True, is_active=True).first()
client = Client(HTTP_HOST="localhost")

if user:
    client.force_login(user)
    print("Authenticated as:", user.username)
else:
    print("No active superuser found.")

paths = [
    "/staff/products/",
    "/staff/products/add/",
    "/staff/orders/",
    "/staff/quotes/",
    "/staff/boss/staff/",
    "/staff/boss/activity/",
]

for path in paths:
    try:
        response = client.get(path)
        print(f"HTTP {response.status_code} | {path}")
    except Exception as exc:
        print(f"ERROR | {path} | {type(exc).__name__}: {exc}")
