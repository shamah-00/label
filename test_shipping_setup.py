import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")

import django
django.setup()

from products.models import ShippingRule, ShippingSystemSettings

print("\n=== SHIPPING SYSTEM CHECK ===")

settings = ShippingSystemSettings.objects.first()
print("Settings record:", "FOUND" if settings else "MISSING")

if settings:
    print("Shipping enabled:", settings.enabled)

rules = ShippingRule.objects.filter(active=True)
print("Active rules:", rules.count())

for rule in rules:
    print("\nRule:", rule.name)
    print("Country:", rule.country)
    print("Base fee:", rule.base_fee)
    print("Per lb:", rule.fee_per_lb)
    print("Handling:", rule.handling_fee)
    print("Free shipping threshold:", rule.free_shipping_threshold)

print("\n=== CHECKOUT URLS ===")
from django.urls import reverse
for name in ["shipping_quote", "checkout", "order_success"]:
    try:
        print(name + ":", reverse(name))
    except Exception as exc:
        print(name + ":", "ERROR -", exc)
