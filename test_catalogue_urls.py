import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")
django.setup()

from django.test import Client

client = Client()
queries = [
    "waste",
    "government",
    "construction",
    "pool",
    "truck_motor_car",
]

failed = []
for industry in queries:
    response = client.get("/products/", {"industry": industry})
    print(f"{industry}: HTTP {response.status_code}")
    if response.status_code >= 500:
        failed.append(industry)

if failed:
    raise SystemExit("Catalogue request failed: " + ", ".join(failed))

print("All tested catalogue requests avoided server errors.")
