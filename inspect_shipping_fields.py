import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")

import django
django.setup()

from products.models import ShippingRule, ShippingSystemSettings

print("=== SHIPPING RULE FIELDS ===")
for field in ShippingRule._meta.fields:
    print(f"{field.name}: {field.__class__.__name__}")

print("\n=== SHIPPING SETTINGS FIELDS ===")
for field in ShippingSystemSettings._meta.fields:
    print(f"{field.name}: {field.__class__.__name__}")

print("\n=== SAVED RULE VALUES ===")
rule = ShippingRule.objects.filter(active=True).first()
if rule:
    for field in rule._meta.fields:
        print(f"{field.name} = {getattr(rule, field.name, None)}")
else:
    print("No active shipping rule found.")
