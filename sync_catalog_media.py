from pathlib import Path
import shutil

BASE_DIR = Path(__file__).resolve().parent
SOURCE = BASE_DIR / "products" / "static"
DESTINATION = BASE_DIR / "media" / "products"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"}

if not SOURCE.is_dir():
    raise SystemExit(f"ERROR: Catalogue image source not found: {SOURCE}")

copied = 0
already_present = 0

for source_file in SOURCE.rglob("*"):
    if not source_file.is_file() or source_file.suffix.lower() not in IMAGE_EXTENSIONS:
        continue

    relative_path = source_file.relative_to(SOURCE)
    destination_file = DESTINATION / relative_path

    if destination_file.exists():
        already_present += 1
        continue

    destination_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, destination_file)
    copied += 1

print(f"Catalogue image sync complete. Copied: {copied}; already present: {already_present}.")
