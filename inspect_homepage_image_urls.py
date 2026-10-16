import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

BASE = "http://127.0.0.1:8000/"

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "img":
            a = dict(attrs)
            if a.get("src"):
                self.images.append((a["src"], a.get("alt", "")))

try:
    with urllib.request.urlopen(BASE, timeout=15) as response:
        html = response.read().decode("utf-8", errors="replace")
        print("Homepage HTTP:", response.status)
except Exception as exc:
    print("Could not reach the local website:", exc)
    raise SystemExit(1)

parser = Parser()
parser.feed(html)

print("\nIMAGE URLS RENDERED IN HOMEPAGE HTML")
print("=" * 65)

for src, alt in parser.images:
    path = urlparse(urljoin(BASE, src)).path
    kind = (
        "WEBP PREVIEW" if "_trimmed.webp" in path
        else "WEBP" if path.lower().endswith(".webp")
        else "PNG ORIGINAL" if path.lower().endswith(".png")
        else "OTHER"
    )
    print(f"{kind:14} | {path} | alt={alt[:55]}")

print("\nTotal <img> tags:", len(parser.images))
print("This check reads the page only; no files were changed.")
