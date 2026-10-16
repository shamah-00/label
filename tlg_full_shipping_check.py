import os
import ast
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPORT = Path(os.environ["TLG_SHIPPING_REPORT"])
out = []

def add(value=""):
    out.append(str(value))

def section(title):
    add()
    add("=" * 75)
    add(title)
    add("=" * 75)

def read(path):
    try:
        return path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        return f"[Unable to read: {exc}]"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")
import django
django.setup()

from django.apps import apps
from django.urls import reverse

section("THE LABEL GROUP: SHIPPING AND CHECKOUT INSPECTION")
add(f"Project: {BASE}")
add(f"Django: {django.get_version()}")
add("Mode: READ-ONLY. This script does not intentionally change source or database records.")

# Models and database
section("1. MODELS AND DATABASE")
for name in ["ShippingRule", "ShippingSystemSettings", "Order", "OrderItem", "Shipment", "Product"]:
    try:
        model = apps.get_model("products", name)
        add(f"\n{name} | table={model._meta.db_table} | records={model.objects.count()}")
        add("Fields: " + ", ".join(f.name for f in model._meta.fields))
        if name in ["ShippingRule", "ShippingSystemSettings"]:
            for obj in model.objects.all()[:10]:
                add("  SAVED: " + ", ".join(
                    f"{field.name}={getattr(obj, field.name, None)}"
                    for field in model._meta.fields
                ))
    except Exception as exc:
        add(f"\n{name}: unavailable: {exc}")

# Full relevant functions from products/views.py
section("2. PRODUCT SHIPPING AND CHECKOUT FUNCTIONS")
path = BASE / "products" / "views.py"
if path.exists():
    source = read(path)
    lines = source.splitlines()
    try:
        tree = ast.parse(source)
        wanted = [
            "shipping_quote", "checkout", "order_success",
            "cart", "add_to_cart", "update_cart", "remove_from_cart"
        ]
        nodes = [
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in wanted
        ]
        if not nodes:
            add("No matching top-level functions found.")
        for node in nodes:
            add(f"\n--- {node.name} (lines {node.lineno}-{node.end_lineno}) ---")
            add("\n".join(lines[node.lineno-1:node.end_lineno]))
    except Exception as exc:
        add(f"Could not parse views.py: {exc}")
        for i, line in enumerate(lines, 1):
            if any(k in line.lower() for k in ["shipping", "checkout", "order_success"]):
                add(f"{i}: {line}")
else:
    add("products/views.py NOT FOUND")

# Staff order/shipping functions
section("3. STAFF ORDER AND SHIPPING FUNCTIONS")
path = BASE / "staff" / "views.py"
if path.exists():
    source = read(path)
    lines = source.splitlines()
    try:
        tree = ast.parse(source)
        nodes = [
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and any(k in node.name.lower() for k in ["shipping", "order", "shipment", "quote"])
        ]
        if not nodes:
            add("No matching staff functions found.")
        for node in nodes:
            add(f"\n--- {node.name} (lines {node.lineno}-{node.end_lineno}) ---")
            add("\n".join(lines[node.lineno-1:node.end_lineno]))
    except Exception as exc:
        add(f"Could not parse staff/views.py: {exc}")
else:
    add("staff/views.py NOT FOUND")

# URL patterns
section("4. URL ROUTES")
for filename in ["products/urls.py", "staff/urls.py", "swiftcart/urls.py"]:
    path = BASE / filename
    add(f"\n--- {filename} ---")
    if path.exists():
        for i, line in enumerate(read(path).splitlines(), 1):
            if any(k in line.lower() for k in [
                "shipping", "checkout", "order", "shipment", "include("
            ]):
                add(f"{i}: {line}")
    else:
        add("File not found.")

# Reverse checks
section("5. NAMED URL CHECKS")
for name, args in [
    ("shipping_quote", []),
    ("checkout", []),
    ("order_success", [1]),
    ("staff_orders", []),
    ("staff_order_detail", [1]),
]:
    try:
        add(f"{name}: {reverse(name, args=args)}")
    except Exception as exc:
        add(f"{name}: unavailable: {exc}")

# Templates, limited to useful matching lines
section("6. SHIPPING, CHECKOUT AND ORDER TEMPLATE REFERENCES")
count = 0
for folder in ["templates", "products/templates", "staff/templates"]:
    root = BASE / folder
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in [".html", ".js", ".css"]:
            continue
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except Exception:
            continue
        matches = [
            f"{i}: {line.strip()}"
            for i, line in enumerate(lines, 1)
            if any(k in line.lower() for k in [
                "shipping_quote", "shipping_cost", "shipping_weight",
                "checkout", "tracking_number", "staff_shipping", "ups"
            ])
        ]
        if matches:
            add(f"\n--- {path.relative_to(BASE)} ---")
            add("\n".join(matches[:40]))
            count += 1
if count == 0:
    add("No matching template references found in scanned folders.")

# Admin and settings references
section("7. ADMIN AND SETTINGS REFERENCES")
for filename in ["products/admin.py", "swiftcart/settings.py"]:
    path = BASE / filename
    add(f"\n--- {filename} ---")
    if path.exists():
        for i, line in enumerate(read(path).splitlines(), 1):
            if any(k in line.lower() for k in [
                "shipping", "order", "shipment", "installed_apps", "ups"
            ]):
                add(f"{i}: {line}")

# Write the report
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text("\n".join(out), encoding="utf-8")

print("AUDIT FINISHED")
print(f"Report saved: {REPORT}")
print(f"Report size: {REPORT.stat().st_size:,} bytes")
print()
print("QUICK SUMMARY")
for line in out:
    if any(term in line for term in [
        "ShippingRule |", "ShippingSystemSettings |",
        "Order |", "OrderItem |", "Shipment |",
        "shipping_quote:", "checkout:", "order_success:",
        "staff_orders:", "staff_order_detail:"
    ]):
        print(line)
print()
print("No source code or database records were intentionally changed.")
