import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")

import django
django.setup()

from products.models import ShippingRule, ShippingSystemSettings
from django.urls import reverse

print("=== SHIPPING CONFIGURATION ===")

settings = ShippingSystemSettings.objects.first()
print("Shipping enabled:", settings.enabled if settings else "NO SETTINGS")
if settings:
    print("Default flat fee:", settings.default_flat_fee)
    print("Default per lb:", settings.default_per_lb_fee)
    print("Default handling fee:", settings.default_handling_fee)
    print("Default free shipping threshold:", settings.default_free_shipping_threshold)

print("\n=== ACTIVE SHIPPING RULES ===")
for rule in ShippingRule.objects.filter(active=True).order_by("-priority"):
    print(
        f"{rule.name}: country={rule.country}, "
        f"flat=${rule.flat_fee}, per_lb=${rule.per_lb_fee}, "
        f"handling=${rule.handling_fee}, "
        f"free_at=${rule.free_shipping_threshold}"
    )

print("\n=== URL CHECK ===")
for name in ["shipping_quote", "checkout", "order_success"]:
    try:
        print(f"{name}: {reverse(name)}")
    except Exception as exc:
        print(f"{name}: ERROR - {exc}")
