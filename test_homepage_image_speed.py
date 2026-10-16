import re
import time
import urllib.request
import urllib.error
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
from statistics import median

BASE = "http://127.0.0.1:8000/"

class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "img":
            attrs = dict(attrs)
            src = attrs.get("src")
            if src:
                self.images.append({
                    "src": src,
                    "alt": attrs.get("alt", ""),
                    "loading": attrs.get("loading", "eager")
                })

def fetch(url):
    request = urllib.request.Request(
        url, headers={"User-Agent": "TheLabelGroup-ImageSpeedTest/1.0"}
    )
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read()
        elapsed = (time.perf_counter() - start) * 1000
        return response.status, body, elapsed, response.headers.get("Content-Type", "")

print("THE LABEL GROUP — LOCAL HOMEPAGE SPEED TEST")
print("=" * 65)

try:
    status, html, page_ms, content_type = fetch(BASE)
except Exception as exc:
    print("Could not open the local website:", exc)
    print("Make sure Django is running in another PowerShell window:")
    print("  .\\venv\\Scripts\\python.exe manage.py runserver")
    raise SystemExit(1)

print(f"Homepage status: HTTP {status}")
print(f"Homepage response: {page_ms:.1f} ms")
print(f"HTML size: {len(html) / 1024:.1f} KB")
print(f"Content type: {content_type}")

parser = ImageParser()
parser.feed(html.decode("utf-8", errors="replace"))

urls = []
seen = set()
for item in parser.images:
    url = urljoin(BASE, item["src"])
    if url not in seen:
        seen.add(url)
        urls.append((url, item))

print(f"\nUnique <img> URLs: {len(urls)}")
print("-" * 65)

results = []
for url, item in urls:
    try:
        status, body, elapsed, content_type = fetch(url)
        size_kb = len(body) / 1024
        results.append((url, status, size_kb, elapsed, item))
        print(
            f"HTTP {status} | {size_kb:8.1f} KB | {elapsed:7.1f} ms | "
            f"{urlparse(url).path}"
        )
    except Exception as exc:
        print(f"FAILED | {urlparse(url).path} | {exc}")

if results:
    sizes = [r[2] for r in results]
    times = [r[3] for r in results]
    total_kb = sum(sizes)
    failures = sum(1 for r in results if r[1] != 200)

    print("\nSUMMARY")
    print("-" * 65)
    print(f"Images fetched successfully: {len(results) - failures}/{len(results)}")
    print(f"Total image payload: {total_kb / 1024:.2f} MB")
    print(f"Average image size: {sum(sizes) / len(sizes):.1f} KB")
    print(f"Largest image: {max(sizes):.1f} KB")
    print(f"Median image response: {median(times):.1f} ms")
    print(f"Non-200 image responses: {failures}")

    print("\nLargest 5 images:")
    for url, status, size_kb, elapsed, item in sorted(
        results, key=lambda r: r[2], reverse=True
    )[:5]:
        print(f"  {size_kb:.1f} KB | {urlparse(url).path}")

print("\nNote: these are local measurements, not public internet or mobile results.")
