from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
from time import perf_counter
import os

BASE = "http://127.0.0.1:8000/"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}

class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "img":
            a = dict(attrs)
            src = a.get("src", "").strip()
            if src and not src.startswith("data:"):
                self.images.append((src, a.get("alt", ""), a.get("loading", "")))
            srcset = a.get("srcset", "")
            if srcset:
                first = srcset.split(",")[0].strip().split(" ")[0]
                if first and not first.startswith("data:"):
                    self.images.append((first, "srcset image", a.get("loading", "")))

print("=" * 65)
print("THE LABEL GROUP — IMAGE PERFORMANCE CHECK")
print("=" * 65)

print("\n1. LOCAL IMAGE INVENTORY")
roots = [Path("media"), Path("products/static"), Path("static")]
files = []
for root in roots:
    if root.exists():
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
                try:
                    files.append((p, p.stat().st_size))
                except OSError:
                    pass

if files:
    total = sum(size for _, size in files)
    print(f"Image files found: {len(files)}")
    print(f"Total image storage: {total / 1024 / 1024:.2f} MB")
    print("\nLargest images:")
    for p, size in sorted(files, key=lambda x: x[1], reverse=True)[:15]:
        print(f"{size / 1024:9.1f} KB | {p}")
else:
    print("No images found in media/, products/static/, or static/.")

print("\n2. HOMEPAGE RESPONSE")
try:
    start = perf_counter()
    req = Request(BASE, headers={"User-Agent": "LabelGroupImageSpeedTest/1.0"})
    with urlopen(req, timeout=10) as response:
        html = response.read()
        status = response.status
        content_type = response.headers.get("Content-Type", "")
    elapsed = (perf_counter() - start) * 1000
    print(f"Homepage: HTTP {status}")
    print(f"Response time: {elapsed:.1f} ms")
    print(f"HTML downloaded: {len(html) / 1024:.1f} KB")
    if "text/html" not in content_type:
        print("Warning: response does not appear to be HTML.")
except Exception as e:
    print(f"Could not load homepage: {type(e).__name__}: {e}")
    print("Make sure Terminal 1 is still running Django.")
    raise SystemExit(1)

parser = ImageParser()
parser.feed(html.decode("utf-8", errors="replace"))
unique = list(dict.fromkeys(item[0] for item in parser.images))
print(f"\n3. HOMEPAGE IMAGE DOWNLOADS ({len(unique)} unique image URLs)")

results = []
for src in unique[:30]:
    url = urljoin(BASE, src)
    if urlparse(url).scheme not in ("http", "https"):
        continue
    try:
        start = perf_counter()
        req = Request(url, headers={"User-Agent": "LabelGroupImageSpeedTest/1.0"})
        with urlopen(req, timeout=15) as response:
            data = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
        ms = (perf_counter() - start) * 1000
        results.append((src, status, ms, len(data), content_type))
        print(f"HTTP {status} | {ms:8.1f} ms | {len(data)/1024:8.1f} KB | {src}")
    except Exception as e:
        print(f"FAILED | {src} | {type(e).__name__}: {e}")

if results:
    good = [r for r in results if r[1] == 200]
    print("\n4. SUMMARY")
    print(f"Images tested: {len(results)}")
    print(f"Successful (HTTP 200): {len(good)}")
    print(f"Failed/non-200: {len(results)-len(good)}")
    if good:
        times = sorted(r[2] for r in good)
        sizes = sorted(r[3] for r in good)
        print(f"Fastest image: {times[0]:.1f} ms")
        print(f"Median image response: {times[len(times)//2]:.1f} ms")
        print(f"Largest downloaded image: {max(sizes)/1024:.1f} KB")
        print(f"Average downloaded image: {sum(sizes)/len(sizes)/1024:.1f} KB")
else:
    print("\nNo image URLs could be tested from the homepage.")
print("\nNote: local timings are not the same as public internet/mobile timings.")
