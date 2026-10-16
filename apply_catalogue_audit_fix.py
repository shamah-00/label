from pathlib import Path

path = Path("products/views.py")
source = path.read_text(encoding="utf-8-sig")

old = "        products = products.filter(industry__in=matching_industries)"

new = '''        if industry_filter == "construction":
            construction_codes = [f"C{i:03d}" for i in range(1, 21)]
            products = products.filter(
                category__iexact="construction",
                product_code__in=construction_codes,
            )
        elif industry_filter == "waste":
            waste_codes = [
                "031A", "032", "042R", "043", "062",
                "066", "071", "072", "074", "089",
                "301", "305", "306", "310", "315",
                "335", "337", "338", "343", "344",
            ]
            products = products.filter(
                industry__in=matching_industries,
                product_code__in=waste_codes,
            )
        elif industry_filter in ("motor", "truck", "truck_motor_car"):
            motor_codes = [
                "312", "320", "333", "362", "DGO",
                "DHO", "DMO", "I711", "NCU",
                *[f"T{i:03d}" for i in range(10, 21)],
            ]
            products = products.filter(
                industry__in=matching_industries,
                product_code__in=motor_codes,
            )
        else:
            products = products.filter(industry__in=matching_industries)'''

if source.count(old) != 1:
    raise SystemExit(
        f"Expected one catalogue filter line; found {source.count(old)}. "
        "No changes made."
    )

path.write_text(source.replace(old, new, 1), encoding="utf-8")
print("Catalogue filters updated.")
