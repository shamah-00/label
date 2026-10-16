from pathlib import Path
from products.models import Product

print("=== PRODUCTS CURRENTLY MARKED CONSTRUCTION ===")
for p in Product.objects.filter(industry__iexact="construction").order_by("product_code", "id"):
    print(
        "ID:", p.id,
        "| Code:", p.product_code,
        "| Name:", p.name,
        "| Category:", p.category,
        "| Industry:", repr(p.industry),
    )

print("\n=== PRODUCTS WITH CONSTRUCTION CATEGORY ===")
for p in Product.objects.filter(category__iexact="construction").order_by("product_code", "id"):
    print(
        "ID:", p.id,
        "| Code:", p.product_code,
        "| Name:", p.name,
        "| Category:", p.category,
        "| Industry:", repr(p.industry),
    )

print("\n=== PRODUCT LIST VIEW SOURCE ===")
source = Path("products/views.py").read_text(encoding="utf-8").splitlines()
for i, line in enumerate(source):
    if "def product_list" in line or "industry" in line.lower() or "category" in line.lower():
        start = max(0, i - 3)
        end = min(len(source), i + 7)
        print(f"\n--- lines {start + 1}-{end} ---")
        for j in range(start, end):
            print(f"{j + 1}: {source[j]}")
