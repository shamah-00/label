import os
from pathlib import Path
from collections import Counter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")
import django
django.setup()

from products.models import Product

extensions = Counter()
missing_standard = []
missing_trimmed = []

for product in Product.objects.exclude(image="").iterator():
    original = Path(product.image.path)
    extensions[original.suffix.lower()] += 1

    # Match the current template's URL slicing behavior exactly.
    url = product.image.url
    expected_standard_url = url[:-4] + ".webp"
    expected_trimmed_url = url[:-4] + "_trimmed.webp"

    # Convert the generated URL suffix to a filesystem path.
    standard_name = expected_standard_url.rsplit("/", 1)[-1]
    trimmed_name = expected_trimmed_url.rsplit("/", 1)[-1]

    if not (original.parent / standard_name).is_file():
        missing_standard.append((original.name, standard_name))

    if not (original.parent / trimmed_name).is_file():
        missing_trimmed.append((original.name, trimmed_name))

print("PRODUCT IMAGE EXTENSIONS:")
for ext, count in sorted(extensions.items()):
    print(f"  {ext or '(no extension)'}: {count}")

print(f"\nMissing standard previews requested by cart: {len(missing_standard)}")
for original, expected in missing_standard[:10]:
    print(f"  {original} -> {expected}")

print(f"\nMissing trimmed previews requested by homepage: {len(missing_trimmed)}")
for original, expected in missing_trimmed[:10]:
    print(f"  {original} -> {expected}")

print("\nRead-only check complete. No files were changed.")
