from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import traceback

user = get_user_model().objects.filter(username="amos").first()

client = Client(raise_request_exception=True)
client.defaults["HTTP_HOST"] = "localhost"

if user:
    client.force_login(user)
else:
    print("User 'amos' not found. Testing pages without login.")

for name in ("staff_products", "staff_product_add"):
    print("\n==========", name, "==========")
    try:
        response = client.get(reverse(name), HTTP_HOST="localhost")
        print("STATUS:", response.status_code)
        print("REDIRECT:", response.get("Location"))
        if response.status_code >= 400:
            print(response.content.decode("utf-8", errors="replace")[-3000:])
    except Exception:
        traceback.print_exc()
