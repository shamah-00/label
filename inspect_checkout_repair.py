from pathlib import Path
import shutil
from datetime import datetime
import django

django.setup()

from products.models import Order, OrderItem

root = Path.cwd()
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = root / f"checkout_repair_backup_{stamp}"
backup.mkdir(exist_ok=True)

files = [
    root / "products" / "views.py",
    root / "products" / "urls.py",
    root / "products" / "models.py",
    root / "products" / "templates" / "checkout.html",
]

print("\n=== BACKUP ===")
for file in files:
    if file.exists():
        shutil.copy2(file, backup / file.name)
        print(f"Backed up: {file.relative_to(root)}")

print("\n=== ORDER MODEL FIELDS ===")
for model in (Order, OrderItem):
    print(f"\n{model.__name__}:")
    for field in model._meta.fields:
        print(
            f"  {field.name}: {field.get_internal_type()}, "
            f"null={field.null}, blank={field.blank}"
        )

print("\n=== CART AND CHECKOUT FUNCTIONS ===")
views = (root / "products" / "views.py").read_text(encoding="utf-8")
for line_no, line in enumerate(views.splitlines(), 1):
    if line.lstrip().startswith("def ") and any(
        word in line.lower()
        for word in ("cart", "checkout", "order", "custom_order")
    ):
        print(f"{line_no}: {line.strip()}")

print("\n=== URLS ===")
print((root / "products" / "urls.py").read_text(encoding="utf-8"))

print("\nNo application code was changed.")
print(f"Backup folder: {backup}")
