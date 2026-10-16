from pathlib import Path
from PIL import Image, ImageChops

root = Path("media/products")
files = sorted(root.rglob("*.webp"))

print("WEBP WHITE-MARGIN REPORT")
print("=" * 80)

for path in files:
    with Image.open(path) as im:
        rgb = im.convert("RGB")
        white = Image.new("RGB", rgb.size, (255, 255, 255))
        diff = ImageChops.difference(rgb, white)
        diff = diff.point(lambda p: 255 if p > 35 else 0)
        bbox = diff.getbbox()

        if not bbox:
            print(f"CHECK MANUALLY | {path} | image appears white")
            continue

        left, top, right, bottom = bbox
        margins = (
            round(left / im.width * 100, 1),
            round(top / im.height * 100, 1),
            round((im.width - right) / im.width * 100, 1),
            round((im.height - bottom) / im.height * 100, 1),
        )

        if max(margins) >= 3:
            print(f"{path}")
            print(f"  size={im.width}x{im.height}, margins L/T/R/B={margins}%")

print(f"\nTotal WebP images checked: {len(files)}")
print("No files were changed.")
