import os
import ast
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")
import django
django.setup()

from django.apps import apps
from django.urls import reverse, get_resolver

BASE = Path(__file__).resolve().parent
out = []
def p(s=""):
    out.append(str(s))
def section(s):
    p("\n" + "=" * 65 + "\n" + s + "\n" + "=" * 65)

# 1. Actual shipping models and saved configuration
section("1. SHIPPING MODEL FIELDS AND SAVED VALUES")
for name in ["ShippingRule", "ShippingSystemSettings", "Order", "OrderItem", "Shipment", "Product"]:
    try:
        model = apps.get_model("products", name)
    except LookupError:
        p(f"\n{name}: NOT FOUND")
        continue
    p(f"\n{name}:")
    p("Fields: " + ", ".join(f.name for f in model._meta.fields))
    try:
        p(f"Record count: {model.objects.count()}")
        if name in ["ShippingRule", "ShippingSystemSettings"]:
            for obj in model.objects.all()[:10]:
                p("  " + ", ".join(f"{f.name}={getattr(obj, f.name, None)}" for f in model._meta.fields))
    except Exception as e:
        p(f"Database error: {e}")

# 2. Only relevant view functions, with line numbers
section("2. SHIPPING AND CHECKOUT VIEWS")
path = BASE / "products" / "views.py"
if path.exists():
    src = path.read_text(encoding="utf-8-sig")
    lines = src.splitlines()
    try:
        tree = ast.parse(src)
        nodes = [
            n for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and any(k in n.name.lower() for k in [
                "shipping", "checkout", "order_success", "cart", "ups"
            ])
        ]
        for n in nodes:
            p(f"\n--- {n.name}, lines {n.lineno}-{n.end_lineno} ---")
            p("\n".join(lines[n.lineno-1:n.end_lineno]))
    except Exception as e:
        p(f"Could not parse views.py: {e}")
        for i, line in enumerate(lines, 1):
            if any(k in line.lower() for k in ["shipping", "checkout", "order_success", "ups"]):
                p(f"{i}: {line}")

# 3. URL routes relevant to shipping and orders
section("3. RELEVANT URLS")
for file in ["products/urls.py", "staff/urls.py", "swiftcart/urls.py"]:
    path = BASE / file
    p(f"\n--- {file} ---")
    if path.exists():
        for i, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            if any(k in line.lower() for k in ["shipping", "checkout", "order", "shipment", "include("]):
                p(f"{i}: {line}")

# 4. Shipping-related staff view functions
section("4. STAFF SHIPPING AND ORDER VIEWS")
path = BASE / "staff" / "views.py"
if path.exists():
    src = path.read_text(encoding="utf-8-sig")
    lines = src.splitlines()
    try:
        tree = ast.parse(src)
        nodes = [
            n for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and any(k in n.name.lower() for k in ["shipping", "order", "shipment", "quote"])
        ]
        for n in nodes:
            p(f"\n--- {n.name}, lines {n.lineno}-{n.end_lineno} ---")
            p("\n".join(lines[n.lineno-1:n.end_lineno]))
    except Exception as e:
        p(f"Could not parse staff/views.py: {e}")

# 5. Shipping references in templates, settings and admin
section("5. TEMPLATE, SETTINGS AND ADMIN REFERENCES")
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
            f"{i}: {line.strip()}" for i, line in enumerate(lines, 1)
            if any(k in line.lower() for k in [
                "shipping_quote", "shipping_cost", "shipping_rule",
                "shipping_weight", "checkout", "tracking_number",
                "staff_shipping", "ups"
            ])
        ]
        if matches:
            p(f"\n--- {path.relative_to(BASE)} ---")
            p("\n".join(matches[:35]))

for file in ["products/admin.py", "swiftcart/settings.py"]:
    path = BASE / file
    p(f"\n--- {file} ---")
    if path.exists():
        for i, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            if any(k in line.lower() for k in [
                "shipping", "order", "shipment", "installed_apps", "ups"
            ]):
                p(f"{i}: {line}")

# 6. URL reverse checks
section("6. URL NAME CHECKS")
for name, args in [
    ("shipping_quote", []), ("checkout", []),
    ("order_success", [1]), ("staff_orders", []),
    ("staff_order_detail", [1])
]:
    try:
        p(f"{name}: {reverse(name, args=args)}")
    except Exception as e:
        p(f"{name}: unavailable ({e})")

report = Path(os.environ["TLG_REPORT"])
report.write_text("\n".join(out), encoding="utf-8")
print("SUMMARY GENERATED")
print("Report:", report)
print("Characters:", sum(len(x) for x in out))
print("Sections:", sum(1 for x in out if x.startswith("=" * 20)))
