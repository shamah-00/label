from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction

from .models import (
Product,
Order,
OrderItem,
QuoteRequest,
QuoteRequestItem,
CollectionCalendarStickerOrder,
)

from .forms import (
QuoteRequestForm,
CollectionCalendarStickerOrderForm,
)

def home(request):rn industry = request.GET.get("industry")
 category = request.GET.get("category")
 search_query = request.GET.get("q")

```
products = Product.objects.filter(
    is_available=True
).order_by("-created_at")

if industry:
    products = products.filter(industry=industry)

if category:
    products = products.filter(category=category)

if search_query:
    products = products.filter(name__icontains=search_query)

featured_codes = [
    "DGO",
    "320",
    "066",
    "043",
    "C001",
    "C016",
    "P001",
    "P010",
    "G001",
    "G006",
]

featured_products_queryset = Product.objects.filter(
    product_code__in=featured_codes,
    is_available=True,
)

featured_lookup = {
    product.product_code: product
    for product in featured_products_queryset
}

featured_products = [
    featured_lookup[code]
    for code in featured_codes
    if code in featured_lookup
]

return render(
    request,
    "home.html",
    {
        "featured_products": featured_products,
        "products": products,
        "selected_industry": industry,
        "selected_category": category,
        "search_query": search_query,
    },
)
```

def industry_products(request, industry):
products = Product.objects.filter(
industry=industry,
is_available=True,
).order_by("-created_at")

```
return render(
    request,
    "products/industry_products.html",
    {
        "products": products,
        "industry": industry,
    },
)
```

def product_detail(request, product_id):
product = get_object_or_404(
Product,
id=product_id,
is_available=True,
)

```
return render(
    request,
    "products/product_detail.html",
    {
        "product": product,
    },
)
```

def add_to_cart(request, product_id):
product = get_object_or_404(
Product,
id=product_id,
is_available=True,
)

```
cart = request.session.get("cart", {})
product_id_str = str(product_id)

quantity = int(request.POST.get("quantity", 1))

if quantity < 1:
    quantity = 1

cart[product_id_str] = cart.get(product_id_str, 0) + quantity

request.session["cart"] = cart
request.session.modified = True

messages.success(
    request,
    f"{product.name} has been added to your cart.",
)

return redirect("cart")
```

def cart(request):
cart_data = request.session.get("cart", {})
cart_items = []
total = Decimal("0.00")

```
for product_id, quantity in cart_data.items():
    product = Product.objects.filter(
        id=product_id,
        is_available=True,
    ).first()

    if not product:
        continue

    quantity = int(quantity)
    price = product.discount_price or product.price
    subtotal = price * quantity

    cart_items.append(
        {
            "product": product,
            "quantity": quantity,
            "price": price,
            "subtotal": subtotal,
        }
    )

    total += subtotal

return render(
    request,
    "products/cart.html",
    {
        "cart_items": cart_items,
        "total": total,
    },
)
```

def update_cart(request, product_id):
cart_data = request.session.get("cart", {})
product_id_str = str(product_id)

```
if product_id_str in cart_data:
    quantity = int(request.POST.get("quantity", 1))

    if quantity <= 0:
        del cart_data[product_id_str]
    else:
        cart_data[product_id_str] = quantity

request.session["cart"] = cart_data
request.session.modified = True

return redirect("cart")
```

def remove_from_cart(request, product_id):
cart_data = request.session.get("cart", {})
product_id_str = str(product_id)

```
if product_id_str in cart_data:
    del cart_data[product_id_str]

request.session["cart"] = cart_data
request.session.modified = True

return redirect("cart")
```

def clear_cart(request):
request.session["cart"] = {}
request.session.modified = True

```
return redirect("cart")
```

def checkout(request):
cart_data = request.session.get("cart", {})

```
if not cart_data:
    messages.warning(request, "Your cart is empty.")
    return redirect("cart")

cart_items = []
total = Decimal("0.00")

for product_id, quantity in cart_data.items():
    product = Product.objects.filter(
        id=product_id,
        is_available=True,
    ).first()

    if not product:
        continue

    quantity = int(quantity)
    price = product.discount_price or product.price
    subtotal = price * quantity

    cart_items.append(
        {
            "product": product,
            "quantity": quantity,
            "price": price,
            "subtotal": subtotal,
        }
    )

    total += subtotal

if not cart_items:
    messages.warning(
        request,
        "Your cart does not contain any available products.",
    )
    return redirect("cart")

if request.method == "POST":
    with transaction.atomic():
        order = Order.objects.create(
            total_amount=total,
            shipping_cost=Decimal("0.00"),
            currency="USD",
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["quantity"],
                unit_price=item["price"],
                subtotal=item["subtotal"],
            )

    request.session["cart"] = {}
    request.session.modified = True

    return redirect(
        "order_success",
        order_id=order.id,
    )

return render(
    request,
    "products/checkout.html",
    {
        "cart_items": cart_items,
        "total": total,
    },
)
```

def order_success(request, order_id):
order = get_object_or_404(Order, id=order_id)

```
return render(
    request,
    "products/order_success.html",
    {
        "order": order,
    },
)
```

def add_to_quote(request, product_id):
product = get_object_or_404(
Product,
id=product_id,
is_available=True,
)

```
quote_cart_data = request.session.get("quote_cart", {})
product_id_str = str(product_id)

quantity = int(request.POST.get("quantity", 1))

if quantity < 1:
    quantity = 1

quote_cart_data[product_id_str] = (
    quote_cart_data.get(product_id_str, 0) + quantity
)

request.session["quote_cart"] = quote_cart_data
request.session.modified = True

messages.success(
    request,
    f"{product.name} has been added to your quote request.",
)

return redirect("quote_cart")
```

def quote_cart(request):
quote_cart_data = request.session.get("quote_cart", {})
quote_items = []

```
for product_id, quantity in quote_cart_data.items():
    product = Product.objects.filter(
        id=product_id,
        is_available=True,
    ).first()

    if not product:
        continue

    quote_items.append(
        {
            "product": product,
            "quantity": int(quantity),
        }
    )

return render(
    request,
    "products/quote_cart.html",
    {
        "quote_items": quote_items,
    },
)
```

def update_quote(request, product_id):
quote_cart_data = request.session.get("quote_cart", {})
product_id_str = str(product_id)

```
if product_id_str in quote_cart_data:
    quantity = int(request.POST.get("quantity", 1))

    if quantity <= 0:
        del quote_cart_data[product_id_str]
    else:
        quote_cart_data[product_id_str] = quantity

request.session["quote_cart"] = quote_cart_data
request.session.modified = True

return redirect("quote_cart")
```

def remove_from_quote(request, product_id):
quote_cart_data = request.session.get("quote_cart", {})
product_id_str = str(product_id)

```
if product_id_str in quote_cart_data:
    del quote_cart_data[product_id_str]

request.session["quote_cart"] = quote_cart_data
request.session.modified = True

return redirect("quote_cart")
```

def clear_quote(request):
request.session["quote_cart"] = {}
request.session.modified = True

```
return redirect("quote_cart")
```

def request_quote(request):
quote_cart_data = request.session.get("quote_cart", {})

```
if not quote_cart_data:
    messages.warning(
        request,
        "Your quote cart is empty.",
    )
    return redirect("quote_cart")

if request.method == "POST":
    form = QuoteRequestForm(request.POST)

    if form.is_valid():
        with transaction.atomic():
            quote_request = form.save()

            for product_id, quantity in quote_cart_data.items():
                product = Product.objects.filter(
                    id=product_id,
                    is_available=True,
                ).first()

                if product:
                    QuoteRequestItem.objects.create(
                        quote_request=quote_request,
                        product=product,
                        quantity=int(quantity),
                    )

        request.session["quote_cart"] = {}
        request.session.modified = True

        return redirect(
            "quote_success",
            quote_id=quote_request.id,
        )
else:
    form = QuoteRequestForm()

return render(
    request,
    "products/request_quote.html",
    {
        "form": form,
    },
)
```

def quote_success(request, quote_id):
quote_request = get_object_or_404(
QuoteRequest,
id=quote_id,
)

```
return render(
    request,
    "products/quote_success.html",
    {
        "quote_request": quote_request,
    },
)
```

def collection_calendar_stickers(request):
if request.method == "POST":
form = CollectionCalendarStickerOrderForm(
request.POST,
request.FILES,
)

```
    if form.is_valid():
        order = form.save()

        return redirect(
            "collection_calendar_stickers_success",
            order_id=order.id,
        )
else:
    form = CollectionCalendarStickerOrderForm()

return render(
    request,
    "products/collection_calendar_stickers.html",
    {
        "form": form,
    },
)
```

def collection_calendar_stickers_success(request, order_id):
order = get_object_or_404(
CollectionCalendarStickerOrder,
id=order_id,
)

```
return render(
    request,
    "products/collection_calendar_stickers_success.html",
    {
        "order": order,
    },
)
```

def product_list(request):
return home(request)

def shipping_view(request):
return render(
request,
"shipping.html",
)

