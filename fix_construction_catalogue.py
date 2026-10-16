from pathlib import Path

path = Path("products/views.py")
source = path.read_text(encoding="utf-8-sig")

old = "        products = products.filter(industry__in=matching_industries)"
new = '''        if industry_filter == "construction":
            construction_codes = [
                f"C{i:03d}" for i in range(1, 21)
            ]
            products = products.filter(
                category__iexact="construction",
                product_code__in=construction_codes,
            )
        else:
            products = products.filter(industry__in=matching_industries)'''

count = source.count(old)
if count != 1:
    raise SystemExit(
        f"Expected exactly one industry-filter line, found {count}. "
        "No changes were made."
    )

path.write_text(source.replace(old, new, 1), encoding="utf-8")
print("Updated Construction catalogue filtering.")
