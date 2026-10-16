import inspect
from products import views
from products.models import Order, OrderItem

print("\n=== REQUIRED ORDER FIELDS ===")
for model in (Order, OrderItem):
    print(f"\n{model.__name__}")
    for field in model._meta.fields:
        if field.name not in ("id", "created_at", "updated_at"):
            print(f"{field.name}: required={not field.blank and not field.null}, default={field.default!r}")

print("\n=== CART FUNCTIONS ===")
for name in ("add_to_cart", "cart", "update_cart", "remove_from_cart", "clear_cart"):
    fn = getattr(views, name, None)
    if fn:
        print(f"\n--- {name} ---")
        print(inspect.getsource(fn))

print("\n=== CHECKOUT TEMPLATE FORM ===")
from pathlib import Path
p = Path("products/templates/checkout.html")
if p.exists():
    lines = p.read_text(encoding="utf-8-sig").splitlines()
    for i, line in enumerate(lines, 1):
        if "<form" in line or "</form>" in line or "method=" in line or "action=" in line or "csrf_token" in line:
            print(f"{i}: {line.strip()}")
