from pathlib import Path

files = [
    Path("products/templates/home.html"),
    Path("products/templates/home_new.html"),
    Path("products/templates/product_list.html"),
    Path("products/templates/cart.html"),
]

for path in files:
    if not path.exists():
        continue

    print("\n" + "=" * 85)
    print("FILE:", path)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    hits = [
        i for i, line in enumerate(lines)
        if "<img" in line.lower()
        or "image.url" in line.lower()
        or "webp" in line.lower()
        or "background-image" in line.lower()
    ]

    if not hits:
        print("No matching image markup found.")
        continue

    shown = set()
    for i in hits:
        for j in range(max(0, i - 1), min(len(lines), i + 3)):
            if j not in shown:
                print(f"{j + 1}: {lines[j].strip()}")
                shown.add(j)
        print()
