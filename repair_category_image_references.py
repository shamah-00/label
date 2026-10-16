from pathlib import Path
from datetime import datetime
import re
import subprocess
import sys

root = Path.cwd()

pairs = [
    ("truck and motors.jpeg", "truck and motors.webp"),
    ("waste and company.jpeg", "waste and company.webp"),
    ("construction.jpeg", "construction.webp"),
    ("pool decal.jpeg", "pool decal.webp"),
    ("government contractor.jpeg", "government contractor.webp"),
]

search_roots = [
    root / "products" / "templates",
    root / "products" / "static",
]

extensions = {".html", ".css", ".js"}
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
changed = 0
missing_previews = []

print("THE LABEL GROUP — SAFE CATEGORY IMAGE REPAIR")
print("=" * 55)

for original, preview in pairs:
    found = any(
        p.is_file() and p.name.lower() == preview.lower()
        for folder in search_roots
        if folder.exists()
        for p in folder.rglob("*")
    )
    if not found:
        missing_previews.append(preview)
        print(f"WARNING: Preview file not found: {preview}")

for folder in search_roots:
    if not folder.exists():
        continue

    for file in folder.rglob("*"):
        if not file.is_file() or file.suffix.lower() not in extensions:
            continue

        try:
            before = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        after = before

        for original, preview in pairs:
            # Replace the filename only, preserving its directory and quoting.
            after = re.sub(
                re.escape(original),
                lambda match: preview,
                after,
                flags=re.IGNORECASE,
            )

        if after != before:
            backup = file.with_name(file.name + f".before_webp_{stamp}")
            backup.write_text(before, encoding="utf-8")
            file.write_text(after, encoding="utf-8")
            changed += 1
            print(f"UPDATED: {file.relative_to(root)}")
            print(f"  Backup: {backup.name}")

print(f"\nFiles updated: {changed}")
print(f"Missing category previews: {len(missing_previews)}")

if changed == 0:
    print(
        "No matching category image references were found. "
        "No template files were changed."
    )

print("\nRunning Django system check...")
result = subprocess.run(
    [sys.executable, "manage.py", "check"],
    cwd=root,
)
print("\nDjango check exit code:", result.returncode)
