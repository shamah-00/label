from pathlib import Path
from PIL import Image

roots = [Path("media"), Path("products/static"), Path("static")]
extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
files = []

for root in roots:
    if root.exists():
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in extensions:
                try:
                    size = path.stat().st_size
                    with Image.open(path) as im:
                        width, height = im.size
                        fmt = im.format or path.suffix.upper()
                    files.append((size, path, width, height, fmt))
                except Exception:
                    pass

print("IMAGE DIMENSIONS AND FILE SIZES")
print("-" * 90)
for size, path, width, height, fmt in sorted(files, reverse=True)[:25]:
    print(f"{size/1024:8.1f} KB | {width:5} x {height:<5} | {fmt:<6} | {path}")

print(f"\nTotal image files inspected: {len(files)}")
