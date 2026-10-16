import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")

import django
django.setup()

from django.conf import settings
from django.test import Client, override_settings

hosts = list(dict.fromkeys([
    "localhost",
    "127.0.0.1",
    *[h for h in settings.ALLOWED_HOSTS if h and h != "*"]
]))

industries = [
    "waste",
    "government",
    "construction",
    "pool",
    "truck_motor_car",
]

failures = []

for host in hosts:
    print(f"\nTesting with HTTP_HOST={host}")
    with override_settings(ALLOWED_HOSTS=[host]):
        client = Client(raise_request_exception=True)
        for industry in industries:
            try:
                response = client.get(
                    "/products/",
                    {"industry": industry},
                    HTTP_HOST=host,
                )
                print(f"  {industry}: HTTP {response.status_code}")
                if response.status_code >= 500 or response.status_code == 400:
                    failures.append((host, industry, response.status_code))
            except Exception as exc:
                failures.append((host, industry, repr(exc)))
                print(f"  {industry}: ERROR {exc!r}")

if failures:
    print("\nFAILURES:")
    for failure in failures:
        print(failure)
    raise SystemExit(1)

print("\nAll five catalogue requests passed host validation and returned without server errors.")
