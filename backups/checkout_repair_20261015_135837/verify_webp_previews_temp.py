import os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")

import django
django.setup()

from products.models import Product

print("THE LABEL GROUP — IMAGE OPTIMIZATION CHECK")
print("=" * 65)

checked = 0
missing_webp = []
missing_trimmed = []
missing_original = []

for product in Product.objects.exclude(image="").iterator():
    try:
        original = Path(product.image.path)
        checked += 1

        webp = original.with_suffix(".webp")
        trimmed = original.with_name(original.stem + "_trimmed.webp")

        if not original.is_file():
            missing_original.append(str(original))
        if not webp.is_file():
            missing_webp.append(str(webp))
        if not trimmed.is_file():
            missing_trimmed.append(str(trimmed))
    except (ValueError, OSError) as exc:
        print(f"Could not check product {product.pk}: {exc}")

print(f"\nProducts with image records checked: {checked}")
print(f"Missing original files: {len(missing_original)}")
print(f"Missing standard WebP previews: {len(missing_webp)}")
print(f"Missing trimmed WebP previews: {len(missing_trimmed)}")

for label, paths in [
    ("MISSING ORIGINAL FILES", missing_original),
    ("MISSING STANDARD WEBP FILES (cart)", missing_webp),
    ("MISSING TRIMMED WEBP FILES (homepage)", missing_trimmed),
]:
    print(f"\n{label} — showing up to 12")
    for path in paths[:12]:
        print("  " + path)
    if not paths:
        print("  None")

print("\nLOGO FILE CHECK")
for path in [
    Path("products/static/products/logo 2 (1).png"),
    Path("products/static/logo 2 (1).png"),
]:
    print(f"{'FOUND' if path.is_file() else 'NOT FOUND'}: {path}")

print("\nRead-only check complete. No files were changed.")
