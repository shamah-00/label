from pathlib import Path
from datetime import datetime
import shutil
from django.test import Client

files = [
    Path("products/templates/checkout.html"),
    Path("products/templates/order_success.html"),
]
backup = Path("checkout_marker_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
backup.mkdir(exist_ok=True)

for path in files:
    if path.exists():
        original = path.read_text(encoding="utf-8-sig")
        shutil.copy2(path, backup / path.name)
        cleaned = original.replace("```", "")
        path.write_text(cleaned, encoding="utf-8")
        print(path, "markers removed:", original.count("```"))

client = Client()
from products.models import Product
product = Product.objects.filter(is_available=True).first()
session = client.session
session["cart"] = {str(product.pk): 1} if product else {}
session.save()

response = client.get("/checkout/", HTTP_HOST="localhost")
print("Checkout status:", response.status_code)
print("Response bytes:", len(response.content))
print("Contains form:", b"<form" in response.content.lower())
print("Still contains backticks:", b"```" in response.content)
print("Backup folder:", backup.resolve())
