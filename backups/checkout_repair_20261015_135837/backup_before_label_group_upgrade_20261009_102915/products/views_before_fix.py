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

def home(request):
industry = request.GET.get("industry")
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
    products = products.filter(
        name__icontains=search_query
    )

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

featured_products = Product.objects.filter(
    product_code__in=featured_codes,
    is_available=True
)

featured_lookup = {
    product.product_code: product
    for product in featured_products
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
    }
)
```

def industry_products(request, industry):
products = Product.objects.filter(
industry=industry,
is_available=True
).order_by("-created_at")

```
industry_names = dict(Product.INDUSTRY_CHOICES)

industry_name = industry_names.get(
    industry,
    "Products"
)

return render(
    request,
    "industry_products.html",
    {
        "products": products,
        "industry": industry,
        "industry_name": industry_name,
    }
)
```

def product_detail(request, product_id):
product = get_object_or_404(
Product,
id=product_id,
is_available=True
)

```
return render(
    request,
    "product_detail.html",
    {
        "product": product
    }
)
```

# ============================================================

# SHOPPING CART

# ============================================================

def add_to_cart(request, product_id):
product = get_object_or_404(
Product,
id=product_id,
is_available=True
)

```
if product.price is None and product.discount_price is None:
    messages.warning(
        request,
        "This product is available by quote only."
    )

    return redirect(
        "product_detail",
        product_id=product.id
    )

cart = request.session.get(
    "cart",
    {}
)

product_key = str(product.id)

if product_key in cart:
    cart[product_key]["quantity"] += 1
else:
    cart[product_key] = {
        "quantity": 1
    }

request.session["cart"] = cart
request.session.modified = True

messages.success(
    request,
    f"{product.name} has been added to your cart."
)

return redirect("cart")
```

def cart(request):
cart_data = request.session.get(
"cart",
{}
)

```
products = Product.objects.filter(
    id__in=cart_data.keys(),
    is_available=True
)

cart_items = []
subtotal = Decimal("0.00")

for product in products:
    product_key = str(product.id)

    quantity = cart_data.get(
        product_key,
        {}
    ).get(
        "quantity",
        1
    )

    unit_price = (
        product.discount_price
        if product.discount_price is not None
        else product.price
    )

    if unit_price is None:
        continue

    item_total = unit_price * quantity

    cart_items.append(
        {
            "product": product,
            "quantity": quantity,
            "unit_price": unit_price,
            "item_total": item_total,
        }
    )

    subtotal += item_total

cart_items.sort(
    key=lambda item: item["product"].id
)

total_quantity = sum(
    item["quantity"]
    for item in cart_items
)

return render(
    request,
    "cart.html",
    {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "total_quantity": total_quantity,
    }
)
```

def update_cart(request, product_id):
if request.method != "POST":
return redirect("cart")

```
product = get_object_or_404(
    Product,
    id=product_id,
    is_available=True
)

cart_data = request.session.get(
    "cart",
    {}
)

product_key = str(product.id)

if product_key not in cart_data:
    return redirect("cart")

try:
    quantity = int(
        request.POST.get(
            "quantity",
            1
        )
    )
except (TypeError, ValueError):
    quantity = 1

if quantity < 1:
    del cart_data[product_key]
else:
    cart_data[product_key]["quantity"] = quantity

request.session["cart"] = cart_data
request.session.modified = True

return redirect("cart")
```

def remove_from_cart(request, product_id):
product_key = str(product_id)

```
cart_data = request.session.get(
    "cart",
    {}
)

if product_key in cart_data:
    del cart_data[product_key]

request.session["cart"] = cart_data
request.session.modified = True

messages.success(
    request,
    "Product removed from your cart."
)

return redirect("cart")
```

def clear_cart(request):
request.session["cart"] = {}
request.session.modified = True

```
messages.success(
    request,
    "Your shopping cart has been cleared."
)

return redirect("cart")
```

# ============================================================

# CHECKOUT

# ============================================================

def checkout(request):
cart_data = request.session.get(
"cart",
{}
)

```
if not cart_data:
    messages.warning(
        request,
        "Your shopping cart is empty."
    )

    return redirect("cart")

products = Product.objects.filter(
    id__in=cart_data.keys(),
    is_available=True
)

checkout_items = []
subtotal = Decimal("0.00")

for product in products:
    product_key = str(product.id)

    quantity = cart_data.get(
        product_key,
        {}
    ).get(
        "quantity",
        1
    )

    unit_price = (
        product.discount_price
        if product.discount_price is not None
        else product.price
    )

    if unit_price is None:
        continue

    item_total = unit_price * quantity

    checkout_items.append(
        {
            "product": product,
            "quantity": quantity,
            "unit_price": unit_price,
            "item_total": item_total,
        }
    )

    subtotal += item_total

if not checkout_items:
    messages.warning(
        request,
        "Your cart does not contain any products available for purchase."
    )

    return redirect("cart")

if request.method == "POST":
    customer_name = request.POST.get(
        "customer_name",
        ""
    ).strip()

    customer_email = request.POST.get(
        "customer_email",
        ""
    ).strip()

    customer_phone = request.POST.get(
        "customer_phone",
        ""
    ).strip()

    shipping_address = request.POST.get(
        "shipping_address",
        ""
    ).strip()

    shipping_city = request.POST.get(
        "shipping_city",
        ""
    ).strip()

    shipping_state = request.POST.get(
        "shipping_state",
        ""
    ).strip()

    shipping_postal_code = request.POST.get(
        "shipping_postal_code",
        ""
    ).strip()

    shipping_country = request.POST.get(
        "shipping_country",
        ""
    ).strip()

    notes = request.POST.get(
        "notes",
        ""
    ).strip()

    if not customer_name:
        messages.error(
            request,
            "Please enter your full name."
        )

        return redirect("checkout")

    if not customer_email:
        messages.error(
            request,
            "Please enter your email address."
        )

        return redirect("checkout")

    if not customer_phone:
        messages.error(
            request,
            "Please enter your phone number."
        )

        return redirect("checkout")

    if not shipping_address:
        messages.error(
            request,
            "Please enter your shipping address."
        )

        return redirect("checkout")

    if not shipping_city:
        messages.error(
            request,
            "Please enter your city."
        )

        return redirect("checkout")

    if not shipping_country:
        messages.error(
            request,
            "Please enter your country."
        )

        return redirect("checkout")

    shipping_cost = Decimal("0.00")
    total = subtotal + shipping_cost

    with transaction.atomic():

        order = Order.objects.create(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_state=shipping_state,
            shipping_postal_code=shipping_postal_code,
            shipping_country=shipping_country,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total=total,
            currency="USD",
            status="pending",
            notes=notes,
        )

        for item in checkout_items:

            product = item["product"]
            quantity = item["quantity"]
            unit_price = item["unit_price"]
            item_total = item["item_total"]

            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                total_price=item_total,
                currency="USD",
            )

    request.session["cart"] = {}
    request.session.modified = True

    return redirect(
        "order_success",
        order_id=order.id
    )

total_quantity = sum(
    item["quantity"]
    for item in checkout_items
)

return render(
    request,
    "checkout.html",
    {
        "checkout_items": checkout_items,
        "subtotal": subtotal,
        "total_quantity": total_quantity,
    }
)
```

def order_success(request, order_id):
order = get_object_or_404(
Order,
id=order_id
)

```
return render(
    request,
    "order_success.html",
    {
        "order": order,
    }
)
```

# ============================================================

# QUOTE CART

# ============================================================

def add_to_quote(request, product_id):
product = get_object_or_404(
Product,
id=product_id,
is_available=True
)

```
quote_cart = request.session.get(
    "quote_cart",
    {}
)

product_key = str(product.id)

if product_key in quote_cart:
    quote_cart[product_key]["quantity"] += 1
else:
    quote_cart[product_key] = {
        "quantity": 1,
    }

request.session["quote_cart"] = quote_cart
request.session.modified = True

messages.success(
    request,
    f"{product.name} has been added to your quote."
)

return redirect("quote_cart")
```

def quote_cart(request):
quote_cart_data = request.session.get(
"quote_cart",
{}
)

```
products = Product.objects.filter(
    id__in=quote_cart_data.keys(),
    is_available=True
)

quote_items = []

for product in products:
    product_key = str(product.id)

    quantity = quote_cart_data.get(
        product_key,
        {}
    ).get(
        "quantity",
        1
    )

    quote_items.append(
        {
            "product": product,
            "quantity": quantity,
        }
    )

quote_items.sort(
    key=lambda item: item["product"].id
)

total_quantity = sum(
    item["quantity"]
    for item in quote_items
)

return render(
    request,
    "quote_cart.html",
    {
        "quote_items": quote_items,
        "total_quantity": total_quantity,
    }
)
```

def update_quote(request, product_id):
if request.method != "POST":
return redirect("quote_cart")

```
product = get_object_or_404(
    Product,
    id=product_id,
    is_available=True
)

quote_cart = request.session.get(
    "quote_cart",
    {}
)

product_key = str(product.id)

if product_key not in quote_cart:
    return redirect("quote_cart")

try:
    quantity = int(
        request.POST.get(
            "quantity",
            1
        )
    )
except (TypeError, ValueError):
    quantity = 1

if quantity < 1:
    del quote_cart[product_key]
else:
    quote_cart[product_key]["quantity"] = quantity

request.session["quote_cart"] = quote_cart
request.session.modified = True

return redirect("quote_cart")
```

def remove_from_quote(request, product_id):
product_key = str(product_id)

```
quote_cart = request.session.get(
    "quote_cart",
    {}
)

if product_key in quote_cart:
    del quote_cart[product_key]

request.session["quote_cart"] = quote_cart
request.session.modified = True

messages.success(
    request,
    "Product removed from your quote."
)

return redirect("quote_cart")
```

def clear_quote(request):
request.session["quote_cart"] = {}
request.session.modified = True

```
messages.success(
    request,
    "Your quote cart has been cleared."
)

return redirect("quote_cart")
```

def request_quote(request):
quote_cart_data = request.session.get(
"quote_cart",
{}
)

```
if not quote_cart_data:
    messages.warning(
        request,
        "Your quote cart is empty. Please select at least one product first."
    )

    return redirect("quote_cart")

products = Product.objects.filter(
    id__in=quote_cart_data.keys(),
    is_available=True
)

quote_items = []

for product in products:
    product_key = str(product.id)

    quantity = quote_cart_data.get(
        product_key,
        {}
    ).get(
        "quantity",
        1
    )

    quote_items.append(
        {
            "product": product,
            "quantity": quantity,
        }
    )

quote_items.sort(
    key=lambda item: item["product"].id
)

if request.method == "POST":
    form = QuoteRequestForm(
        request.POST,
        request.FILES
    )

    if form.is_valid():
        quote_request = form.save()

        for item in quote_items:
            product = item["product"]
            quantity = item["quantity"]

            QuoteRequestItem.objects.create(
                quote_request=quote_request,
                product=product,
                product_name=product.name,
                product_code=product.product_code,
                quantity=quantity,
            )

        request.session["quote_cart"] = {}
        request.session.modified = True

        return redirect(
            "quote_success",
            quote_id=quote_request.id
        )

else:
    form = QuoteRequestForm()

total_quantity = sum(
    item["quantity"]
    for item in quote_items
)

return render(
    request,
    "request_quote.html",
    {
        "form": form,
        "quote_items": quote_items,
        "total_quantity": total_quantity,
    }
)
```

def quote_success(request, quote_id):
quote_request = get_object_or_404(
QuoteRequest,
id=quote_id
)

```
return render(
    request,
    "quote_success.html",
    {
        "quote_request": quote_request,
    }
)
```

# ============================================================

# COLLECTION CALENDAR STICKERS

# ============================================================

def collection_calendar_stickers(request):

```
if request.method == "POST":

    form = CollectionCalendarStickerOrderForm(
        request.POST
    )

    spam_check = request.POST.get(
        "spam_check",
        ""
    ).strip().lower()

    if spam_check not in ["water is wet", "wet"]:
        form.add_error(
            None,
            "Please answer the spam question correctly."
        )

    if form.is_valid():

        calendar_order = form.save()

        messages.success(
            request,
            "Your Collection Calendar Sticker request has been submitted successfully."
        )

        return redirect(
            "collection_calendar_stickers_success",
            order_id=calendar_order.id
        )

else:
    form = CollectionCalendarStickerOrderForm()

return render(
    request,
    "collection_calendar_stickers.html",
    {
        "form": form,
    }
)
```

def collection_calendar_stickers_success(
request,
order_id
):
calendar_order = get_object_or_404(
CollectionCalendarStickerOrder,
id=order_id
)

```
return render(
    request,
    "collection_calendar_stickers_success.html",
    {
        "calendar_order": calendar_order,
    }
)
```

def product_list(request):
return home(request)

def shipping_view(request):
return render(
request,
"shipping.html"
)
