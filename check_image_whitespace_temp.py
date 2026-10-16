from pathlib import Path
from PIL import Image, ImageChops, ImageStat

root = Path("media/products")
extensions = {".png", ".jpg", ".jpeg", ".webp"}

print("\nPRODUCT IMAGE BORDER CHECK")
print("-" * 65)

checked = 0

for path in root.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in extensions:
        continue

    try:
        with Image.open(path) as image:
            rgb = image.convert("RGB")
            background = Image.new("RGB", rgb.size, "white")
            diff = ImageChops.difference(rgb, background)
            diff = diff.point(lambda p: 255 if p > 35 else 0)
            bbox = diff.getbbox()

            if bbox:
                left, top, right, bottom = bbox
                margins = (
                    round(left / image.width * 100, 1),
                    round(top / image.height * 100, 1),
                    round((image.width - right) / image.width * 100, 1),
                    round((image.height - bottom) / image.height * 100, 1),
                )

                if max(margins) >= 2:
                    print(f"\n{path}")
                    print(f"  Size: {image.width} x {image.height}")
                    print(f"  Approx. white margins L/T/R/B: {margins}%")

            checked += 1

    except Exception:
        pass

print(f"\nChecked {checked} image files.")
print("No files were changed.")
