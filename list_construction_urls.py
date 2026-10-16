from products.models import Product
from django.urls import reverse

qs = Product.objects.filter(
    category="construction",
    product_code__regex=r"^C[0-9]{3}$"
).order_by("product_code", "id")

print("CONSTRUCTION PRODUCTS:", qs.count())

for p in qs:
    try:
        url = reverse("product_detail", args=[p.id])
    except Exception:
        url = f"/products/{p.id}/"

    print("{} | ID {} | {} | http://127.0.0.1:8000{}".format(
        p.product_code, p.id, p.name, url
    ))
