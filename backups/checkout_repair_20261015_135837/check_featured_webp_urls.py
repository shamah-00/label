import urllib.request
from urllib.parse import quote

base = "http://127.0.0.1:8000/media/products/"
names = [
    "trucks/Gasoline Only Red Fuel Sign_trimmed.webp",
    "government/government/Government Contractor Equipment Label_trimmed.webp",
    "government/government/Purple CUI Security Information Label_trimmed.webp",
    "government/government/Sensitive Government Property Label_trimmed.webp",
    "government/government/Government Asset Location Label_trimmed.webp",
    "government/government/Government Property Accountability Label_trimmed.webp",
]

passed = 0
for name in names:
    url = base + quote(name, safe="/")
    try:
        request = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(request, timeout=10) as response:
            size = response.headers.get("Content-Length", "unknown")
            print(f"HTTP {response.status} | {size} bytes | {name}")
            if response.status == 200:
                passed += 1
    except Exception as exc:
        print(f"FAILED | {name} | {exc}")

print(f"\nRESULT: {passed}/{len(names)} previews available")
