import os
from pathlib import Path
from urllib.parse import unquote

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")
import django
django.setup()

from products.models import Product

missing_standard = []
missing_trimmed = []
extensions = set()

for product in Product.objects.exclude(image="").iterator():
    original = Path(product.image.path)
    extensions.add(original.suffix.lower())

    # Decode URL-escaped spaces and other characters before checking disk.
    url_path = unquote(product.image.url.split("?", 1)[0])
    url_name = Path(url_path).name

    standard_name = url_name[:-4] + ".webp"
    trimmed_name = url_name[:-4] + "_trimmed.webp"

    if not (original.parent / standard_name).is_file():
        missing_standard.append(standard_name)

    if not (original.parent / trimmed_name).is_file():
        missing_trimmed.append(trimmed_name)

print("Image extensions:", ", ".join(sorted(extensions)))
print("Products checked:", Product.objects.exclude(image="").count())
print("Missing standard WebP previews:", len(missing_standard))
print("Missing trimmed WebP previews:", len(missing_trimmed))

print("\nFirst 10 missing trimmed previews:")
for name in missing_trimmed[:10]:
    print(" ", name)

print("\nRead-only verification complete. No files were changed.")
