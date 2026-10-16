from collections import Counter
from products.models import Product

products = list(
    Product.objects.filter(product_code__regex=r"^C[0-9]{3}$")
    .order_by("product_code", "id")
)

counts = Counter(p.product_code for p in products)

for p in products:
    if counts[p.product_code] > 1:
        print("-" * 45)
        print("ID:", p.id)
        print("Code:", p.product_code)
        print("Name:", p.name)
        print("Industry:", p.industry)
        print("Category:", p.category)
        print("Description:", repr(p.description))
        print("Size:", p.shape)
        print("Material:", p.material)
        print("Finish:", p.finish)
        print("Price:", p.price)
        print("Image:", p.image.name if p.image else "[NO IMAGE]")
