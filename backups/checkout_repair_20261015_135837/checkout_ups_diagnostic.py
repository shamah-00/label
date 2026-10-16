import os
import traceback
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")
django.setup()

from django.test import Client
from django.urls import reverse
from products.models import Product, Order

print("\n========== CHECKOUT REPAIR DIAGNOSTIC ==========")

try:
    client = Client(raise_request_exception=True)
    product = Product.objects.first()

    if product:
        session = client.session
        session["cart"] = {str(product.pk): 1}
        session.save()
        print("Test cart prepared with product:", product.pk, str(product))
    else:
        print("WARNING: No products exist to test checkout.")

    for path in ("/cart/", "/checkout/"):
        try:
            response = client.get(path, HTTP_HOST="localhost")
            print(f"\n{path}: HTTP {response.status_code}")
            print("Rendered bytes:", len(response.content))
            print("Content preview:", response.content[:250].decode("utf-8", errors="replace"))
        except Exception:
            print(f"\nERROR RENDERING {path}:")
            traceback.print_exc()

except Exception:
    traceback.print_exc()

print("\n========== UPS CONFIGURATION ==========")
for key in ("UPS_CLIENT_ID", "UPS_CLIENT_SECRET", "UPS_ACCOUNT_NUMBER"):
    print(f"{key} configured:", bool(os.environ.get(key)))

print("\n========== LATEST SAVED ORDER ==========")
order = Order.objects.order_by("-created_at").first()
if order:
    print("Order:", order.pk, "| Status:", order.status, "| Total:", order.total)
else:
    print("No orders have been saved yet.")

print("\nDiagnostic complete. No orders or application files were changed.")
