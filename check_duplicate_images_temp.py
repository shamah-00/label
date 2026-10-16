from pathlib import Path
from collections import defaultdict
import hashlib

roots = [Path("media"), Path("products/static"), Path("static")]
groups = defaultdict(list)
extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}

for root in roots:
    if not root.exists():
        continue

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue

        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            groups[digest].append(path)
        except OSError as exc:
            print(f"Could not inspect {path}: {exc}")

duplicates = [paths for paths in groups.values() if len(paths) > 1]

print("\nEXACT DUPLICATE IMAGE FILES")
print("=" * 75)

if not duplicates:
    print("No exact duplicate files found.")
else:
    saved_bytes = 0
    for paths in duplicates:
        size = paths[0].stat().st_size
        saved_bytes += size * (len(paths) - 1)
        print(f"\nDuplicate group ({size / 1024:.1f} KB each):")
        for path in paths:
            print(f"  {path}")

    print(f"\nDuplicate groups: {len(duplicates)}")
    print(f"Potential space saved by keeping one copy of each: {saved_bytes / 1024 / 1024:.2f} MB")
    print("This is a report only. No files were changed or deleted.")

print(f"\nUnique image contents: {len(groups)}")
