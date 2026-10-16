import os
from pathlib import Path
from urllib.request import urlopen

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")

import django
django.setup()

from django.template.loader import get_template

root = Path.cwd()
template_path = root / "products" / "templates" / "home.html"
lines = template_path.read_text(encoding="utf-8").splitlines()

print("=" * 65)
print("1. CATEGORY IMAGE SECTION: home.html lines 1540–1650")
print("=" * 65)
for i in range(1539, min(1650, len(lines))):
    print(f"{i + 1}: {lines[i]}")

print("\n" + "=" * 65)
print("2. DJANGO TEMPLATE RESOLUTION")
print("=" * 65)
template = get_template("products/home.html")
print("Resolved template:", template.origin.name)

print("\n" + "=" * 65)
print("3. ACTUAL RUNNING HOMEPAGE IMAGE URLS")
print("=" * 65)
try:
    with urlopen("http://127.0.0.1:8000/", timeout=10) as response:
        html = response.read().decode("utf-8", errors="replace")
        print("Homepage HTTP:", response.status)
        print("HTML bytes:", len(html.encode("utf-8")))

    import re
    for tag in re.findall(r"<img\b[^>]*>", html, re.I | re.S):
        src = re.search(r"""\bsrc\s*=\s*["'](.*?)["']""", tag, re.I | re.S)
        alt = re.search(r"""\balt\s*=\s*["'](.*?)["']""", tag, re.I | re.S)
        loading = re.search(r"""\bloading\s*=\s*["'](.*?)["']""", tag, re.I | re.S)
        print(
            f"src={src.group(1) if src else '(missing)'}"
            f" | alt={alt.group(1) if alt else ''}"
            f" | loading={loading.group(1) if loading else 'not set'}"
        )
except Exception as exc:
    print("Homepage request failed:", exc)

print("\nNo files were changed.")
