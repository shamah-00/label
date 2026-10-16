from pathlib import Path
from datetime import datetime
import shutil
import re
import os
import django

root = Path.cwd()
checkout = root / "products" / "templates" / "checkout.html"
success = root / "products" / "templates" / "order_success.html"
base = root / "products" / "templates" / "base.html"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")
django.setup()

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = root / f"checkout_template_backup_{stamp}"
backup.mkdir(exist_ok=True)

for p in (checkout, success, base):
    if p.exists():
        shutil.copy2(p, backup / p.name)

if not checkout.exists():
    raise SystemExit("ERROR: checkout.html not found; no templates changed.")

text = checkout.read_text(encoding="utf-8-sig")
base_text = base.read_text(encoding="utf-8-sig") if base.exists() else ""
has_base_blocks = bool(re.search(r"{%\s*block\s+\w+", base_text))

if re.search(r"{%\s*extends\s+['\"]base\.html['\"]\s*%}", text) and not has_base_blocks:
    text = re.sub(r"^\s*{%\s*extends\s+['\"]base\.html['\"]\s*%}\s*", "", text, count=1)
    text = re.sub(r"{%\s*block\s+content\s*%}", "", text, count=1)
    text = re.sub(r"{%\s*endblock\s*%}\s*$", "", text, count=1)
    checkout.write_text(text, encoding="utf-8")
    print("Fixed checkout template inheritance.")
else:
    print("Checkout does not match the incompatible inheritance pattern; left unchanged.")

if success.exists():
    s = success.read_text(encoding="utf-8-sig")
    if re.search(r"{%\s*extends\s+['\"]base\.html['\"]\s*%}", s) and not has_base_blocks:
        s = re.sub(r"^\s*{%\s*extends\s+['\"]base\.html['\"]\s*%}\s*", "", s, count=1)
        s = re.sub(r"{%\s*block\s+content\s*%}", "", s, count=1)
        s = re.sub(r"{%\s*endblock\s*%}\s*$", "", s, count=1)
        s = "<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>Order Confirmation | THE LABEL GROUP</title></head><body>\n" + s + "\n</body></html>"
        success.write_text(s, encoding="utf-8")
        print("Fixed order confirmation template inheritance.")

from django.test import Client
client = Client()
response = client.get("/checkout/", HTTP_HOST="localhost")
print("Checkout HTTP status:", response.status_code)
print("Checkout response bytes:", len(response.content))
print("Contains checkout form:", b"<form" in response.content.lower())
print("Backup folder:", backup)
