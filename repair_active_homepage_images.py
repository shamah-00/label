import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")

import django
django.setup()

from django.template.loader import get_template
from PIL import Image, ImageOps

root = Path.cwd()
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

template = Path(get_template("products/home.html").origin.name)
if not template.is_absolute():
    template = root / template

print("=" * 65)
print("THE LABEL GROUP — HOMEPAGE IMAGE REPAIR")
print("Active template:", template)
print("=" * 65)

if not template.is_file():
    raise SystemExit("STOP: Active homepage template was not found.")

content = template.read_text(encoding="utf-8")
updated = content

# 1. Create a smaller logo copy without changing the original.
logo = root / "products" / "static" / "logo 2 (1).png"
logo_webp = logo.with_suffix(".webp")

if logo.is_file() and not logo_webp.exists():
    try:
        with Image.open(logo) as original:
            image = ImageOps.exif_transpose(original)
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert(
                    "RGBA" if "transparency" in image.info else "RGB"
                )
            image.save(logo_webp, "WEBP", quality=88, method=6)
        print(
            f"LOGO COPY: {logo.stat().st_size / 1024:.1f} KB -> "
            f"{logo_webp.stat().st_size / 1024:.1f} KB"
        )
    except Exception as exc:
        print("Logo conversion skipped:", exc)

if logo_webp.is_file():
    updated = updated.replace("logo 2 (1).png", "logo 2 (1).webp")

# 2. Point category images to the existing WebP copies.
category_pairs = [
    ("truck and motors.jpeg", "truck and motors.webp"),
    ("waste and company.jpeg", "waste and company.webp"),
    ("construction.jpeg", "construction.webp"),
    ("pool decal.jpeg", "pool decal.webp"),
    ("government contractor.jpeg", "government contractor.webp"),
]

static_root = root / "products" / "static"
for old_name, new_name in category_pairs:
    candidates = [
        p for p in static_root.rglob("*")
        if p.is_file() and p.name.lower() == new_name.lower()
    ]
    if not candidates:
        print("SKIPPED missing WebP:", new_name)
        continue

    if old_name in updated:
        updated = updated.replace(old_name, new_name)
        print("CATEGORY UPDATED:", old_name, "->", new_name)

# 3. Change product-card image URLs to the trimmed WebP previews.
product_tags_updated = 0

def repair_product_img(match):
    global product_tags_updated
    tag = match.group(0)

    if "product.image.url" not in tag:
        return tag

    if "_trimmed.webp" not in tag:
        pattern = re.compile(
            r"""src\s*=\s*(["'])\s*\{\{\s*product\.image\.url\s*\}\}\s*\1"""
        )
        replacement = (
            'src="{% with trimmed_path=product.image.url|slice:\":-4\" %}'
            '{{ trimmed_path }}_trimmed.webp{% endwith %}"'
        )
        new_tag, count = pattern.subn(replacement, tag, count=1)

        if count == 0:
            print("NOTICE: Product image tag uses a different src expression.")
            return tag

        tag = new_tag

    if not re.search(r'\bloading\s*=', tag):
        tag = tag[:-1].rstrip() + ' loading="lazy">'

    if not re.search(r'\bdecoding\s*=', tag):
        tag = tag[:-1].rstrip() + ' decoding="async">'

    if not re.search(r'\bonerror\s*=', tag):
        tag = tag[:-1].rstrip() + (
            ' onerror="if(!this.dataset.fallback){'
            'this.dataset.fallback=\'1\';'
            'this.src=\'{{ product.image.url }}\';}">'
        )

    product_tags_updated += 1
    return tag

updated = re.sub(
    r"<img\b[^>]*>",
    repair_product_img,
    updated,
    flags=re.IGNORECASE | re.DOTALL,
)

print("Product image tags updated:", product_tags_updated)

# 4. Back up the active template before changing it.
if updated != content:
    backup = template.with_name(template.name + f".before_image_repair_{stamp}")
    shutil.copy2(template, backup)
    template.write_text(updated, encoding="utf-8")
    print("TEMPLATE UPDATED:", template)
    print("BACKUP CREATED:", backup)
else:
    print("No template changes were needed.")

# 5. Run Django's system check.
print("\n=== DJANGO CHECK ===")
check = subprocess.run(
    [sys.executable, "manage.py", "check"],
    cwd=root,
)
if check.returncode != 0:
    print("WARNING: Django check failed. Restore the template backup if necessary.")
    raise SystemExit(check.returncode)

# 6. Test actual image URLs and measure downloaded image payload.
print("\n=== LIVE HOMEPAGE IMAGE AUDIT ===")
base = "http://127.0.0.1:8000/"

try:
    with urlopen(base, timeout=10) as response:
        html = response.read().decode("utf-8", errors="replace")
        print("Homepage HTTP:", response.status)
except Exception as exc:
    print("Could not reach the development server:", exc)
    print("Restart it with: .\\venv\\Scripts\\python.exe manage.py runserver")
    raise SystemExit(0)

tags = re.findall(r"<img\b[^>]*>", html, re.IGNORECASE | re.DOTALL)
total = 0
success = 0

for tag in tags:
    src_match = re.search(r"""\bsrc\s*=\s*["'](.*?)["']""", tag, re.I | re.S)
    alt_match = re.search(r"""\balt\s*=\s*["'](.*?)["']""", tag, re.I | re.S)
    loading_match = re.search(r"""\bloading\s*=\s*["'](.*?)["']""", tag, re.I)

    if not src_match:
        continue

    image_url = urljoin(base, src_match.group(1))
    try:
        req = Request(image_url, headers={"User-Agent": "TheLabelGroupAudit/1.0"})
        with urlopen(req, timeout=15) as response:
            data = response.read()
            total += len(data)
            success += 1
            print(
                f"HTTP {response.status} | {len(data)/1024:.1f} KB"
                f" | loading={loading_match.group(1) if loading_match else 'not set'}"
                f" | alt={alt_match.group(1) if alt_match else ''}"
            )
    except Exception as exc:
        print("IMAGE FAILED:", image_url, exc)

print(f"\nImages successful: {success}/{len(tags)}")
print(f"Total image payload: {total / 1024 / 1024:.2f} MB")
print("Compare this result with the previous 9.01 MB audit.")
