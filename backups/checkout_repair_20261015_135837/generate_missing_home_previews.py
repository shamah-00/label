import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")

import django
django.setup()

from pathlib import Path
from PIL import Image, ImageOps
from products.models import Product

MAX_SIZE = (1200, 1200)
QUALITY = 80

created = 0
skipped = 0
failed = 0
original_total = 0
preview_total = 0

print("THE LABEL GROUP — HOMEPAGE WEBP PREVIEW GENERATOR")
print("=" * 65)

for product in Product.objects.exclude(image="").iterator():
    try:
        original = Path(product.image.path)
        if not original.is_file():
            print(f"MISSING ORIGINAL: {original}")
            failed += 1
            continue

        preview = original.with_name(original.stem + "_trimmed.webp")

        if preview.exists():
            skipped += 1
            continue

        with Image.open(original) as source:
            image = ImageOps.exif_transpose(source)
            image.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)

            has_alpha = (
                "A" in image.getbands()
                or "transparency" in image.info
            )
            image = image.convert("RGBA" if has_alpha else "RGB")

            # Create exclusively: never overwrite an existing file.
            with preview.open("xb") as output:
                image.save(output, format="WEBP", quality=QUALITY, method=6)

        original_size = original.stat().st_size
        preview_size = preview.stat().st_size
        original_total += original_size
        preview_total += preview_size
        created += 1

        print(
            f"CREATED: {preview.name} | "
            f"{original_size / 1024:.1f} KB -> "
            f"{preview_size / 1024:.1f} KB"
        )

    except Exception as exc:
        print(f"FAILED: {product.name} — {exc}")
        failed += 1

print("\n" + "=" * 65)
print(f"New previews created: {created}")
print(f"Existing previews skipped: {skipped}")
print(f"Failures: {failed}")

if original_total:
    print(f"Processed originals: {original_total / 1024:.1f} KB")
    print(f"Generated previews: {preview_total / 1024:.1f} KB")
    print(
        f"Size reduction: "
        f"{(1 - preview_total / original_total) * 100:.1f}%"
    )

print("\nOriginal print files were not modified.")
