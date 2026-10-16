from pathlib import Path
import re

for filename, patterns in {
    "products/models.py": [r"class Order\b", r"class OrderItem\b"],
    "products/views.py": [r"def checkout\b", r"def order_success\b"],
    "products/urls.py": [r"checkout", r"order_success"],
    "products/templates/checkout.html": [r"shipping_", r"<form", r"Place Order"],
}.items():
    path = Path(filename)
    print("\n" + "=" * 65)
    print("FILE:", filename)
    print("=" * 65)
    if not path.exists():
        print("FILE NOT FOUND")
        continue
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    selected = set()
    for pattern in patterns:
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.I):
                selected.update(range(max(0, i-3), min(len(lines), i+28)))
    previous = -2
    for i in sorted(selected):
        if i > previous + 1:
            print("...")
        print(f"{i+1}: {lines[i]}")
        previous = i

print("\nUPS credentials are not printed for security.")
