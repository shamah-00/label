import re
import urllib.request
from urllib.parse import urljoin, urlparse, unquote
from html.parser import HTMLParser

BASE = "http://127.0.0.1:8000/"

class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "img":
            return
        attrs = dict(attrs)
        src = attrs.get("src", "")
        if src:
            self.images.append({
                "src": src,
                "alt": attrs.get("alt", ""),
                "loading": attrs.get("loading", "eager/default"),
            })

print("FETCHING LIVE HOMEPAGE:", BASE)

try:
    request = urllib.request.Request(
        BASE,
        headers={"User-Agent": "TheLabelGroup-ImageAudit/1.0"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        html = response.read().decode("utf-8", errors="replace")
        print("Homepage HTTP:", response.status)
        print("HTML size:", len(html.encode("utf-8")), "bytes")
except Exception as exc:
    print("Could not fetch homepage:", exc)
    raise SystemExit(1)

parser = ImageParser()
parser.feed(html)

print("\nIMAGE TAGS ACTUALLY RETURNED BY DJANGO:", len(parser.images))
total_bytes = 0
success = 0

for item in parser.images:
    url = urljoin(BASE, item["src"])
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TheLabelGroup-ImageAudit/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read()
            size = len(data)
            total_bytes += size
            success += 1
            path = unquote(urlparse(url).path)
            print(
                f"HTTP {response.status} | {size / 1024:.1f} KB"
                f" | loading={item['loading']} | {path}"
                f" | alt={item['alt']}"
            )
    except Exception as exc:
        print(f"FAILED | {url} | {exc}")

print("\nSUMMARY")
print(f"Images successfully downloaded: {success}/{len(parser.images)}")
print(f"Total image payload: {total_bytes / 1024 / 1024:.2f} MB")
print("Note: this tests the image URLs in the HTML; CSS background images are separate.")
