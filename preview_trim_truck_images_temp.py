from pathlib import Path
from PIL import Image, ImageChops

root = Path("media/products/trucks")
out = Path("media/products/_trim_preview")
out.mkdir(parents=True, exist_ok=True)

files = sorted(root.glob("*.webp"))
created = 0

for path in files:
    with Image.open(path) as original:
        image = original.convert("RGB")
        white = Image.new("RGB", image.size, "white")
        diff = ImageChops.difference(image, white)
        mask = diff.point(lambda p: 255 if p > 35 else 0)
        bbox = mask.getbbox()

        if not bbox:
            print("SKIPPED all-white image:", path.name)
            continue

        left, top, right, bottom = bbox
        width, height = image.size

        # Only trim clear vertical margins; preserve left/right edges.
        # Keep a 1.5% safety margin to avoid cutting artwork.
        pad_x = int(width * 0.015)
        pad_y = int(height * 0.015)

        crop_box = (
            max(0, left - pad_x),
            max(0, top - pad_y),
            min(width, right + pad_x),
            min(height, bottom + pad_y),
        )

        cropped = image.crop(crop_box)
        destination = out / path.name
        cropped.save(destination, "WEBP", quality=92, method=6)

        print(f"{path.name}: {width}x{height} -> {cropped.width}x{cropped.height}")
        created += 1

print(f"\nCreated {created} preview images in {out}")
print("Original images and homepage files were not changed.")
