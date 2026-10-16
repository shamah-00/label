from pathlib import Path
from PIL import Image

root = Path("media/products")
shown = 0

print("EXISTING WEBP PREVIEW SAMPLES")
print("=" * 70)

for preview in root.rglob("*_trimmed.webp"):
    original = preview.with_name(preview.name.replace("_trimmed.webp", preview.suffix))
    if not original.is_file():
        # Find the original with the same base name and a common image extension.
        matches = [
            preview.with_name(preview.name.replace("_trimmed.webp", ext))
            for ext in (".png", ".jpg", ".jpeg", ".webp")
        ]
        original = next((p for p in matches if p.is_file()), None)

    try:
        with Image.open(preview) as im:
            preview_size = im.size
            preview_bytes = preview.stat().st_size

        print(f"\nPreview: {preview.name}")
        print(f"  Dimensions: {preview_size[0]} x {preview_size[1]}")
        print(f"  File size: {preview_bytes / 1024:.1f} KB")

        if original:
            with Image.open(original) as im:
                print(f"  Original: {original.name}")
                print(f"  Original dimensions: {im.width} x {im.height}")
                print(f"  Original size: {original.stat().st_size / 1024:.1f} KB")
        else:
            print("  Original file: not located automatically")

        shown += 1
        if shown >= 5:
            break
    except Exception as exc:
        print(f"Could not inspect {preview}: {exc}")

if shown == 0:
    print("No existing trimmed previews were found.")
