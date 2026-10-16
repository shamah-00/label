import os
import re
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")

import django
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.template.loader import get_template
from PIL import Image, ImageOps
from products.models import Product

ROOT = Path.cwd()
STATIC_ROOT = ROOT / "products" / "static"
TEMPLATE_ROOT = ROOT / "products" / "templates"

print("=" * 70)
print("THE LABEL GROUP — IMAGE OPTIMIZATION AND HOMEPAGE CHECK")
print("=" * 70)

# 1. Back up and create lightweight category image copies.
category_names = [
    "truck and motors",
    "waste and company",
    "construction",
    "pool decal",
    "government contractor",
]

created = 0
skipped = 0
failed = 0

print("\n1. CATEGORY IMAGE WEBP COPIES")
for keyword in category_names:
    matches = [
        p for p in STATIC_ROOT.rglob("*")
        if p.is_file()
        and keyword in p.stem.lower()
        and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]

    if not matches:
        print(f"NOT FOUND: {keyword}")
        continue

    for source in matches:
        destination = source.with_suffix(".webp")

        if destination.exists():
            skipped += 1
            print(f"EXISTS: {destination.relative_to(ROOT)}")
            continue

        try:
            with Image.open(source) as original:
                image = ImageOps.exif_transpose(original)
                image.thumbnail((1400, 1400), Image.Resampling.LANCZOS)

                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGBA" if "transparency" in image.info else "RGB")

                image.save(
                    destination,
                    "WEBP",
                    quality=82,
                    method=6
                )

            created += 1
            print(
                f"CREATED: {destination.relative_to(ROOT)} "
                f"({source.stat().st_size / 1024:.1f} KB -> "
                f"{destination.stat().st_size / 1024:.1f} KB)"
            )
        except Exception as exc:
            failed += 1
            print(f"FAILED: {source.name}: {exc}")

print(f"\nCategory copies created: {created}")
print(f"Existing copies skipped: {skipped}")
print(f"Failures: {failed}")

# 2. Check all product preview files.
print("\n2. PRODUCT PREVIEW VERIFICATION")
products = list(Product.objects.exclude(image=""))
missing_standard = []
missing_trimmed = []

for product in products:
    try:
        original = Path(product.image.path)
    except (ValueError, NotImplementedError):
        continue

    standard = original.with_suffix(".webp")
    trimmed = original.with_name(original.stem + "_trimmed.webp")

    if not standard.is_file():
        missing_standard.append((product.name, str(standard)))
    if not trimmed.is_file():
        missing_trimmed.append((product.name, str(trimmed)))

print(f"Products with images: {len(products)}")
print(f"Missing standard previews: {len(missing_standard)}")
print(f"Missing trimmed previews: {len(missing_trimmed)}")

for name, path in (missing_standard + missing_trimmed)[:20]:
    print(f"  MISSING: {name} -> {path}")

# 3. Identify homepage routing and inspect homepage image sources.
print("\n3. HOMEPAGE VIEW AND IMAGE REFERENCES")
for file in [ROOT / "products" / "urls.py", ROOT / "products" / "views.py"]:
    if not file.exists():
        continue

    content = file.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    for index, line in enumerate(lines):
        if re.search(r"home_new\.html|home\.html|def home\b|TemplateView", line):
            start = max(0, index - 2)
            end = min(len(lines), index + 4)
            print(f"\n{file.relative_to(ROOT)}:{index + 1}")
            for number in range(start, end):
                print(f"  {number + 1}: {lines[number].rstrip()}")

candidate_templates = [
    TEMPLATE_ROOT / "home.html",
    TEMPLATE_ROOT / "home_new.html",
]

for template_path in candidate_templates:
    if not template_path.is_file():
        continue

    content = template_path.read_text(encoding="utf-8", errors="replace")
    print(f"\nTEMPLATE: {template_path.relative_to(ROOT)}")

    try:
        get_template(
            str(template_path.relative_to(TEMPLATE_ROOT)).replace("\\", "/")
        )
        print("  Django template parsing: OK")
    except Exception as exc:
        print(f"  Django template loading note: {exc}")

    img_tags = re.findall(r"<img\b[^>]*>", content, flags=re.I | re.S)
    print(f"  Image tags in source: {len(img_tags)}")

    for tag in img_tags:
        src = re.search(r"""\bsrc\s*=\s*["'](.*?)["']""", tag, flags=re.I | re.S)
        alt = re.search(r"""\balt\s*=\s*["'](.*?)["']""", tag, flags=re.I | re.S)
        src_value = src.group(1) if src else "(dynamic or missing src)"
        alt_value = alt.group(1) if alt else "(no alt)"
        if any(word in (src_value + " " + alt_value).lower()
               for word in ["product.image", ".png", ".jpg", ".jpeg", ".webp", "static"]):
            print(f"  src={src_value[:180]} | alt={alt_value[:90]}")

# 4. Django checks.
print("\n4. DJANGO SYSTEM CHECK")
try:
    call_command("check")
except Exception as exc:
    print(f"CHECK FAILED: {exc}")

print("\n" + "=" * 70)
print("REPORT COMPLETE — original images and templates were not overwritten.")
print("New WebP copies, if any, are separate files.")
print("=" * 70)
