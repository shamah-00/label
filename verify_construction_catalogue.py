from products.models import Product

codes = [f"C{i:03d}" for i in range(1, 21)]
items = Product.objects.filter(
    category__iexact="construction",
    product_code__in=codes,
).order_by("product_code")

print("\nConstruction catalogue verification:")
for p in items:
    print(f"{p.product_code} | ID {p.id} | {p.name}")

print(f"\nTotal Construction products: {items.count()}")
