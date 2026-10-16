from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch

User = get_user_model()
user = User.objects.filter(username="amos").first()

client = Client()
client.defaults["HTTP_HOST"] = "127.0.0.1"

if user:
    client.force_login(user)
else:
    print("WARNING: User 'amos' was not found.")

routes = [
    ("staff_products", "/staff/products/"),
    ("staff_product_add", "/staff/products/add/"),
    ("staff_orders", "/staff/orders/"),
    ("staff_quotes", "/staff/quotes/"),
    ("boss_staff_management", "/staff/staff-management/"),
    ("staff_activity_log", "/staff/activity-log/"),
]

for name, fallback in routes:
    try:
        try:
            url = reverse(name)
        except NoReverseMatch:
            url = fallback
            print(f"\n{name}: URL name is missing; testing {url}")

        response = client.get(url, HTTP_HOST="127.0.0.1")
        print(f"{name}: HTTP {response.status_code} | {url}")

        if response.status_code >= 500:
            print(response.content.decode("utf-8", errors="replace")[-1500:])
    except Exception as error:
        print(f"{name}: ERROR {type(error).__name__}: {error}")
