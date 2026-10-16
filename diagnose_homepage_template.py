import os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")

import django
django.setup()

from django.template.loader import get_template
from django.conf import settings

root = Path.cwd()

print("=" * 65)
print("1. DJANGO TEMPLATE RESOLUTION")
print("=" * 65)

for name in ["products/home.html", "home.html", "products/home_new.html"]:
    try:
        template = get_template(name)
        print(f"{name} -> {template.origin.name}")
    except Exception as exc:
        print(f"{name} -> NOT FOUND ({exc})")

print("\n" + "=" * 65)
print("2. HOMEPAGE TEMPLATES IN THE PROJECT")
print("=" * 65)

for path in root.rglob("home.html"):
    if any(part in {"venv", ".git", "__pycache__"} for part in path.parts):
        continue
    print(path.relative_to(root))

print("\n" + "=" * 65)
print("3. IMAGE REFERENCES IN PRODUCTS/HOME.HTML")
print("=" * 65)

path = root / "products" / "templates" / "home.html"
if path.exists():
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    for i, line in enumerate(lines):
        lower = line.lower()
        if "<img" in lower or "truck and motors" in lower or \
           "waste and company" in lower or "construction.jpeg" in lower or \
           "pool decal" in lower or "government contractor" in lower or \
           "product.image.url" in lower:
            start = max(0, i - 1)
            end = min(len(lines), i + 3)
            print(f"\nLine {i + 1}:")
            for j in range(start, end):
                print(f"{j + 1}: {lines[j].strip()}")
else:
    print("Template file not found.")

print("\n" + "=" * 65)
print("4. TEMPLATE SETTINGS")
print("=" * 65)

for directory in settings.TEMPLATES:
    print("DIRS:", directory.get("DIRS"))
    print("APP_DIRS:", directory.get("APP_DIRS"))

print("\nDiagnostic complete. No files were changed.")
