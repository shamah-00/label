import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")
django.setup()

from products.models import Shipment

print("Django initialized successfully.")
print("Shipment model:", Shipment.__module__)
print("Shipment records:", Shipment.objects.count())
print("\nAvailable shipment fields:")

for field in Shipment._meta.fields:
    print(f"- {field.name}")
