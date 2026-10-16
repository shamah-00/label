from pathlib import Path
import re

path = Path("products/views.py")
source = path.read_text(encoding="utf-8-sig")

# Locate the existing industry filter and determine its actual indentation.
pattern = re.compile(
    r"(?m)^([ \t]*)products = products\.filter\(industry__in=matching_industries\)[ \t]*$"
)
matches = list(pattern.finditer(source))

if len(matches) != 1:
    raise SystemExit(
        f"Expected one original industry filter; found {len(matches)}. "
        "No changes made."
    )

indent = matches[0].group(1)
inner = indent + "    "

lines = [
    indent + 'if industry_filter == "construction":',
    inner + 'construction_codes = [f"C{i:03d}" for i in range(1, 21)]',
    inner + "products = products.filter(",
    inner + '    category__iexact="construction",',
    inner + "    product_code__in=construction_codes,",
    inner + ")",
    indent + 'elif industry_filter == "waste":',
    inner + "waste_codes = [",
    inner + '    "031A", "032", "042R", "043", "062",',
    inner + '    "066", "071", "072", "074", "089",',
    inner + '    "301", "305", "306", "310", "315",',
    inner + '    "335", "337", "338", "343", "344",',
    inner + "]",
    inner + "products = products.filter(",
    inner + "    industry__in=matching_industries,",
    inner + "    product_code__in=waste_codes,",
    inner + ")",
    indent + 'elif industry_filter in ("motor", "truck", "truck_motor_car"):',
    inner + "motor_codes = [",
    inner + '    "312", "320", "333", "362", "DGO",',
    inner + '    "DHO", "DMO", "I711", "NCU",',
    inner + '    *[f"T{i:03d}" for i in range(10, 21)],',
    inner + "]",
    inner + "products = products.filter(",
    inner + "    industry__in=matching_industries,",
    inner + "    product_code__in=motor_codes,",
    inner + ")",
    indent + "else:",
    inner + "products = products.filter(industry__in=matching_industries)",
]

replacement = "\n".join(lines)
updated = pattern.sub(lambda _: replacement, source, count=1)

# Compile before writing so an indentation error cannot be saved.
compile(updated, str(path), "exec")
path.write_text(updated, encoding="utf-8")
print("Catalogue filter syntax validated and saved.")
