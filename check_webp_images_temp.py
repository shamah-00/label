from pathlib import Path
from PIL import Image

root = Path("media/products")
files = list(root.rglob("*.webp"))
missing = []
unreadable = []

for path in files:
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        unreadable.append((str(path), str(exc)))

print("WebP files found:", len(files))
print("Unreadable WebP files:", len(unreadable))

for item in unreadable[:10]:
    print("UNREADABLE:", item[0], "|", item[1])

print("\nSample WebP files:")
for path in files[:12]:
    print(path)
