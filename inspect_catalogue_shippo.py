from pathlib import Path
import os
import re
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")
django.setup()

from django.apps import apps

print("\n========== PRODUCT RECORDS ==========")
for model in apps.get_models():
    fields = {f.name for f in model._meta.get_fields()}
    if {"product_code", "name"}.issubset(fields):
        print("Product model:", model._meta.label)
        print("Fields:", ", ".join(sorted(fields)))
        for prefix in ("P", "G"):
            qs = model.objects.filter(product_code__startswith=prefix).order_by("product_code")
            print(f"\n{prefix} products: {qs.count()}")
            for p in qs:
                print(
                    p.product_code,
                    "|", p.name,
                    "| category:", getattr(p, "category", ""),
                    "| industry:", getattr(p, "industry", ""),
                    "| available:", getattr(p, "is_available", ""),
                    "| image:", bool(getattr(p, "image", None)),
                )

print("\n========== ORDER / SHIPMENT MODELS ==========")
for model in apps.get_models():
    name = model.__name__.lower()
    if "order" in name or "shipment" in name or "shippo" in name:
        print("\n", model._meta.label)
        print(", ".join(f.name for f in model._meta.get_fields()))

print("\n========== SHIPPO / SHIPPING REFERENCES ==========")
roots = [Path("products"), Path("staff"), Path("swiftcart"), Path("templates")]
terms = re.compile(
    r"shippo|shipment|shipping.rate|shipping_label|tracking_number|"
    r"create_shipment|purchase_label|shipping_address",
    re.I,
)
skip = {".git", "venv", "__pycache__", "migrations", "node_modules"}

for root in roots:
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file() or any(part in skip for part in path.parts):
            continue
        if path.suffix not in {".py", ".html", ".txt"}:
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        hits = [i for i, line in enumerate(lines) if terms.search(line)]
        if hits:
            print(f"\n--- {path} ---")
            shown = set()
            for i in hits[:12]:
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    if j not in shown:
                        # Do not print secret values from configuration.
                        line = re.sub(
                            r"(?i)(SHIPPO_API_TOKEN|SHIPPO_API_KEY|API_TOKEN|API_KEY)"
                            r"\s*[:=]\s*['\"][^'\"]+['\"]",
                            r"\1 = '[REDACTED]'",
                            lines[j],
                        )
                        print(f"{j+1}: {line[:240]}")
                        shown.add(j)

print("\n========== DJANGO CHECK ==========")
from django.core.management import call_command
call_command("check")
