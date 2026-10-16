from pathlib import Path

root = Path("media/products")

searches = [
    ("Sensitive Government Property", "Sensitive"),
    ("Government Asset Location", "Asset Location"),
]

for label, keyword in searches:
    print(f"\n{label}")
    print("-" * 60)

    matches = sorted(
        p for p in root.rglob("*")
        if p.is_file()
        and keyword.lower() in p.name.lower()
        and ("trimmed" in p.name.lower() or p.suffix.lower() == ".png")
    )

    if not matches:
        print("No matching files found.")
    else:
        for path in matches:
            print(f"{path} ({path.stat().st_size / 1024:.1f} KB)")
