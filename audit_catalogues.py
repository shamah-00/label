from collections import Counter
from django.core.files.storage import default_storage
from products.models import Product

targets = {"motor", "truck", "truck_motor_car", "waste", "construction"}

products = list(
    Product.objects.filter(industry__in=targets)
    .order_by("industry", "product_code", "id")
)

print("=" * 75)
print("THE LABEL GROUP — CATALOGUE AUDIT")
print("=" * 75)

for industry in ("motor", "truck", "truck_motor_car", "waste", "construction"):
    rows = [p for p in products if (p.industry or "").lower() == industry]
    if not rows:
        continue

    print(f"\n--- INDUSTRY: {industry.upper()} | COUNT: {len(rows)} ---")
    code_counts = Counter((p.product_code or "").strip().upper() for p in rows)

    for p in rows:
        image_name = p.image.name if p.image else ""
        image_ok = default_storage.exists(image_name) if image_name else False
        issues = []

        if not (p.product_code or "").strip():
            issues.append("MISSING CODE")
        if not (p.name or "").strip():
            issues.append("MISSING NAME")
        if not image_name:
            issues.append("NO IMAGE SET")
        elif not image_ok:
            issues.append("IMAGE FILE MISSING")
        if (p.category or "").strip().lower() != industry:
            issues.append("CATEGORY/INDUSTRY DIFFER")
        if code_counts[(p.product_code or "").strip().upper()] > 1:
            issues.append("DUPLICATE CODE IN THIS INDUSTRY")

        print(
            f"ID={p.id} | CODE={p.product_code} | "
            f"NAME={p.name} | CATEGORY={p.category} | "
            f"IMAGE={'OK' if image_ok else 'CHECK'} | "
            f"STOCK={p.stock} | AVAILABLE={p.is_available} | "
            f"ISSUES={', '.join(issues) if issues else 'none detected'}"
        )

print("\n--- SUMMARY BY INDUSTRY FIELD ---")
for industry in ("motor", "truck", "truck_motor_car", "waste", "construction"):
    print(f"{industry}: {sum(1 for p in products if (p.industry or '').lower() == industry)}")

print("\n--- ALL PRODUCTS MARKED FOR THESE INDUSTRIES ---")
print(f"Total records: {len(products)}")
print("Audit complete. No database changes were made.")
