from .models import QuoteRequest
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product

def home(request):
    from django.db.models import Q

    products = Product.objects.filter(is_available=True).order_by("-id")

    industry_filter = request.GET.get("industry", "").strip().lower()

    if industry_filter == "waste":
        products = products.filter(
            Q(id__gte=1, id__lte=60)
        )
    elif industry_filter == "motor":
        products = products.filter(
            Q(id__gte=1, id__lte=60)
        )
    elif industry_filter == "construction":
        products = products.filter(
            Q(id__gte=41, id__lte=60)
        )
    elif industry_filter == "pool":
        products = products.filter(
            Q(id__gte=61, id__lte=80)
        )
    elif industry_filter == "government":
        products = products.filter(
            Q(id__gte=81, id__lte=100)
        )
    elif industry_filter == "other":
        products = products.filter(id__gte=101)

    return render(
        request,
        "products/home.html",
        {
            "products": products,
            "industry_filter": industry_filter,
        },
    )


def product_list(request):
    from django.db.models import Q

    products = Product.objects.filter(
        is_available=True
    ).order_by("id")

    industry = request.GET.get("industry", "").strip().lower()
    search = request.GET.get("search", "").strip()

    category_ranges = {
        "motor": (1, 20),
        "waste": (21, 40),
        "construction": (41, 60),
        "pool": (61, 80),
        "government": (81, 100),
    }

    if industry in category_ranges:
        first_id, last_id = category_ranges[industry]
        products = products.filter(
            id__gte=first_id,
            id__lte=last_id
        )
    elif industry == "other":
        products = products.exclude(
            id__gte=1,
            id__lte=100
        )

    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(brand__icontains=search) |
            Q(category__icontains=search) |
            Q(product_type__icontains=search) |
            Q(product_code__icontains=search)
        )

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "selected_industry": industry,
            "search_query": search,
            "product_count": products.count(),
        },
    )


def industry_products(request, industry_name):
    industry_name = (industry_name or "").strip().lower()

    allowed = {
        "motor": "motor",
        "waste": "waste",
        "construction": "construction",
        "pool": "pool",
        "government": "government",
        "other": "other",
    }

    industry = allowed.get(industry_name)

    if not industry:
        return redirect("product_list")

    from django.http import HttpResponseRedirect
    from django.urls import reverse

    url = reverse("product_list") + "?industry=" + industry
    search = request.GET.get("search", "").strip()

    if search:
        from urllib.parse import quote
        url += "&search=" + quote(search)

    return HttpResponseRedirect(url)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "products/product_detail.html", {'product': product})

def cart(request):
    return render(request, "products/cart.html", {})


def add_to_quote(request, product_id):
    from django.shortcuts import get_object_or_404, redirect

    product = get_object_or_404(Product, id=product_id)

    quote_cart = request.session.get("quote_cart", {})
    product_key = str(product.id)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    quantity = max(quantity, 1)

    quote_cart[product_key] = quote_cart.get(product_key, 0) + quantity

    request.session["quote_cart"] = quote_cart
    request.session.modified = True

    return redirect("quote_cart")

def remove_from_quote(request, product_id):
    quote_cart = request.session.get("quote_cart", {})
    product_key = str(product_id)

    if product_key in quote_cart:
        del quote_cart[product_key]
        request.session["quote_cart"] = quote_cart
        request.session.modified = True

    return redirect("quote_cart")
def quote_cart(request):
    from .models import Product
    from django.shortcuts import render

    cart = request.session.get("quote_cart", {})
    products_by_id = {}
    valid_cart = {}

    for product_id, raw_quantity in cart.items():
        try:
            product_id = int(product_id)
            quantity = max(1, int(raw_quantity))
        except (TypeError, ValueError):
            continue
        valid_cart[str(product_id)] = quantity

    products = Product.objects.filter(pk__in=valid_cart.keys())
    for product in products:
        products_by_id[str(product.pk)] = product

    quote_items = []
    for product_id, quantity in valid_cart.items():
        product = products_by_id.get(product_id)
        if product is None:
            continue
        product.quote_quantity = quantity
        quote_items.append({
            "product": product,
            "quantity": quantity,
        })

    request.session["quote_cart"] = {
        str(item["product"].pk): item["quantity"]
        for item in quote_items
    }

    return render(request, "products/quote_cart.html", {
        "quote_items": quote_items,
        "quote_products": [item["product"] for item in quote_items],
        "products": [item["product"] for item in quote_items],
        "quote_count": sum(item["quantity"] for item in quote_items),
        "quote_cart_empty": not bool(quote_items),
    })


def shipping(request):
    return render(request, "products/shipping.html", {})

def add_to_cart(request, product_id):
    from django.shortcuts import get_object_or_404, redirect
    from .models import Product

    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})
    key = str(product_id)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    quantity = max(1, quantity)
    cart[key] = int(cart.get(key, 0)) + quantity

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def cart(request):
    from django.shortcuts import render
    from .models import Product

    session_cart = request.session.get("cart", {})
    products = []

    for product_id, quantity in session_cart.items():
        try:
            product = Product.objects.get(id=int(product_id))
            quantity = max(1, int(quantity))
            products.append({
                "product": product,
                "quantity": quantity,
                "subtotal": product.price * quantity,
            })
        except (Product.DoesNotExist, ValueError, TypeError):
            continue

    total = sum(item["subtotal"] for item in products)

    return render(
        request,
        "cart.html",
        {
            "cart_items": products,
            "cart": products,
            "total": total,
            "cart_total": total,
        },
    )


def update_cart(request, product_id):
    from django.shortcuts import redirect

    cart = request.session.get("cart", {})

    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1

        if quantity > 0:
            cart[str(product_id)] = quantity
        else:
            cart.pop(str(product_id), None)

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def remove_from_cart(request, product_id):
    from django.shortcuts import redirect

    cart = request.session.get("cart", {})
    cart.pop(str(product_id), None)

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def clear_cart(request):
    from django.shortcuts import redirect

    request.session["cart"] = {}
    request.session.modified = True

    return redirect("cart")



def custom_order(request):
    from .models import QuoteRequest, QuoteRequestItem, Product
    from django.shortcuts import render
    from django.db import transaction

    if request.method == "POST":
        customer_name = request.POST.get("customer_name", "").strip()
        customer_email = request.POST.get("customer_email", "").strip()
        customer_phone = request.POST.get("customer_phone", "").strip()

        if not customer_name or not customer_email or not customer_phone:
            return render(request, "products/custom_order.html", {
                "error": "Please provide your name, email address, and phone number.",
            })

        with transaction.atomic():
            quote = QuoteRequest.objects.create(
                customer_name=customer_name,
                company_name=request.POST.get("company_name", "").strip(),
                customer_email=customer_email,
                customer_phone=customer_phone,
                street_address=request.POST.get("street_address", "").strip(),
                address_continued=request.POST.get("address_continued", "").strip(),
                city=request.POST.get("city", "").strip(),
                state=request.POST.get("state", "").strip(),
                postal_code=request.POST.get("postal_code", "").strip(),
                country=request.POST.get("country", "").strip(),
                requirements=request.POST.get("requirements", "").strip(),
                uploaded_file=request.FILES.get("uploaded_file"),
            )

            cart = request.session.get("quote_cart", {})
            for product_id, raw_quantity in cart.items():
                try:
                    product = Product.objects.get(pk=int(product_id))
                    quantity = max(1, int(raw_quantity))
                except (Product.DoesNotExist, TypeError, ValueError):
                    continue

                QuoteRequestItem.objects.create(
                    quote_request=quote,
                    product=product,
                    product_name=str(product),
                    product_code=str(
                        getattr(product, "product_code", "")
                        or getattr(product, "sku", "")
                    ),
                    quantity=quantity,
                )

        request.session["quote_cart"] = {}
        request.session.modified = True
        return render(request, "products/quote_success.html", {
            "quote": quote,
            "quote_id": quote.pk,
        })

    return render(request, "products/custom_order.html", {})









# =========================================================
# SHIPPING QUOTE DESK
# =========================================================

def shipping_quote(request):
    from .models import QuoteRequest, QuoteRequestItem, Product
    from django.shortcuts import render
    from django.db import transaction

    if request.method == "POST":
        customer_name = request.POST.get("customer_name", "").strip()
        customer_email = request.POST.get("customer_email", "").strip()
        customer_phone = request.POST.get("customer_phone", "").strip()

        if not customer_name or not customer_email or not customer_phone:
            return render(request, "products/shipping_quote.html", {
                "error": "Please provide your name, email address, and phone number.",
            })

        with transaction.atomic():
            quote = QuoteRequest.objects.create(
                customer_name=customer_name,
                company_name=request.POST.get("company_name", "").strip(),
                customer_email=customer_email,
                customer_phone=customer_phone,
                street_address=request.POST.get("street_address", "").strip(),
                address_continued=request.POST.get("address_continued", "").strip(),
                city=request.POST.get("city", "").strip(),
                state=request.POST.get("state", "").strip(),
                postal_code=request.POST.get("postal_code", "").strip(),
                country=request.POST.get("country", "").strip(),
                requirements=request.POST.get("requirements", "").strip(),
                uploaded_file=request.FILES.get("uploaded_file"),
            )

            cart = request.session.get("quote_cart", {})
            for product_id, raw_quantity in cart.items():
                try:
                    product = Product.objects.get(pk=int(product_id))
                    quantity = max(1, int(raw_quantity))
                except (Product.DoesNotExist, TypeError, ValueError):
                    continue

                QuoteRequestItem.objects.create(
                    quote_request=quote,
                    product=product,
                    product_name=str(product),
                    product_code=str(
                        getattr(product, "product_code", "")
                        or getattr(product, "sku", "")
                    ),
                    quantity=quantity,
                )

        request.session["quote_cart"] = {}
        request.session.modified = True
        return render(request, "products/quote_success.html", {
            "quote": quote,
            "quote_id": quote.pk,
        })

    return render(request, "products/shipping_quote.html", {})

def custom_orders(request):
    if request.method == 'POST':
        from .models import CustomOrder
        full_name = request.POST.get('full_name')
        company_name = request.POST.get('company_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('street_address', '') + ', ' + request.POST.get('city', '')
        requirements = request.POST.get('requirements')
        artwork = request.FILES.get('artwork')

        CustomOrder.objects.create(
            full_name=full_name,
            company_name=company_name,
            email=email,
            phone=phone,
            address=address,
            requirements=requirements,
            artwork=artwork
        )
        return render(request, 'products/custom_order_success.html', {'full_name': full_name})

    return render(request, 'products/custom_orders.html')











# THE LABEL GROUP: invoice payment page foundation.
# Connect a real payment provider before accepting payments.
def invoice_payment(request):
    from django.shortcuts import render

    invoice_number = ""
    amount = ""
    message = ""

    if request.method == "POST":
        invoice_number = request.POST.get("invoice_number", "").strip()
        amount = request.POST.get("amount", "").strip()

        if not invoice_number:
            message = "Please enter your invoice number."
        else:
            try:
                value = float(amount)
                if value <= 0:
                    raise ValueError
                amount = f"{value:.2f}"
                message = (
                    "Your invoice details are ready. Online payment processing "
                    "must be connected by the site administrator before payment "
                    "can be completed. Please contact THE LABEL GROUP to arrange payment."
                )
            except (TypeError, ValueError):
                message = "Please enter a valid invoice amount in USD."

    return render(
        request,
        "products/invoice_payment.html",
        {
            "invoice_number": invoice_number,
            "amount": amount,
            "message": message,
        },
    )


# ============================================================
# CUSTOMER CHECKOUT AND ORDER CONFIRMATION
# ============================================================


def checkout(request):
    from decimal import Decimal
    import json
    import os
    import urllib.request
    import urllib.error
    from django.contrib import messages
    from django.db import transaction
    from django.shortcuts import render, redirect
    from .models import Product, Order, OrderItem

    def get_items():
        result = []
        for product_id, quantity in request.session.get("cart", {}).items():
            try:
                product = Product.objects.get(pk=int(product_id), is_available=True)
                quantity = max(1, int(quantity))
                result.append({
                    "product": product,
                    "quantity": quantity,
                    "subtotal": product.price * quantity,
                    "total_price": product.price * quantity,
                })
            except (Product.DoesNotExist, ValueError, TypeError):
                continue
        return result

    items = get_items()
    if not items:
        messages.error(request, "Your cart is empty or its products are unavailable.")
        return redirect("cart")

    subtotal = sum((item["subtotal"] for item in items), Decimal("0.00"))
    shipping_cost = Decimal("0.00")
    rates = []
    rate_error = ""

    def get_rates(postal_code, city, state, country):
        token = os.getenv("SHIPPO_API_KEY", "").strip()
        if not token:
            raise ValueError("Shipping rates are temporarily unavailable.")

        parcels = []
        for item in items:
            product = item["product"]
            values = (
                product.shipping_weight_lb,
                product.shipping_length_in,
                product.shipping_width_in,
                product.shipping_height_in,
            )
            if any(value is None for value in values):
                raise ValueError(
                    "Shipping measurements are missing for one or more products. "
                    "Please contact us for a shipping quote."
                )
            if any(value <= 0 for value in values):
                raise ValueError("Invalid shipping measurements on a product.")

            for _ in range(item["quantity"]):
                parcels.append({
                    "length": str(product.shipping_length_in),
                    "width": str(product.shipping_width_in),
                    "height": str(product.shipping_height_in),
                    "distance_unit": "in",
                    "weight": str(product.shipping_weight_lb),
                    "mass_unit": "lb",
                })

        # Multiple packages are passed as separate parcels in one shipment.
        payload = {
            "address_from": {
                "name": "The Label Group LLC",
                "street1": "580 St. James Avenue",
                "city": "Springfield",
                "state": "MA",
                "zip": "01109",
                "country": "US",
                "phone": "413-731-6700",
                "email": "labelgroup@comcast.net",
            },
            "address_to": {
                "street1": request.POST.get("shipping_address", "").strip(),
                "city": city,
                "state": state,
                "zip": postal_code,
                "country": country,
            },
            "parcels": parcels,
            "async": False,
        }

        req = urllib.request.Request(
            "https://api.goshippo.com/shipments/",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "ShippoToken " + token,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))

        found = []
        for rate in data.get("rates", []):
            amount = rate.get("amount")
            if not amount:
                continue
            try:
                price = Decimal(str(amount))
            except Exception:
                continue
            found.append({
                "object_id": rate.get("object_id", ""),
                "provider": rate.get("provider", "Carrier"),
                "service": rate.get("servicelevel", {}).get("name", "Shipping"),
                "amount": price,
                "currency": rate.get("currency", "USD"),
                "estimated_days": rate.get("estimated_days"),
            })
        return found

    context = {
        "checkout_items": items,
        "cart_items": items,
        "items": items,
        "subtotal": subtotal,
        "cart_total": subtotal,
        "shipping_cost": shipping_cost,
        "total": subtotal,
        "grand_total": subtotal,
        "shipping_rates": rates,
        "shipping_rate_error": rate_error,
    }

    if request.method == "POST":
        customer_name = request.POST.get("customer_name", "").strip()
        customer_email = request.POST.get("customer_email", "").strip()
        customer_phone = request.POST.get("customer_phone", "").strip()
        shipping_address = request.POST.get("shipping_address", "").strip()
        shipping_city = request.POST.get("shipping_city", "").strip()
        shipping_state = request.POST.get("shipping_state", "").strip()
        shipping_postal_code = request.POST.get("shipping_postal_code", "").strip()
        shipping_country = request.POST.get("shipping_country", "US").strip().upper()
        notes = request.POST.get("notes", "").strip()
        action = request.POST.get("action", "place_order")

        required = {
            "name": customer_name,
            "email": customer_email,
            "phone": customer_phone,
            "shipping address": shipping_address,
            "city": shipping_city,
            "country": shipping_country,
            "postal code": shipping_postal_code,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            messages.error(request, "Please complete: " + ", ".join(missing) + ".")
            return render(request, "checkout.html", context)

        try:
            rates = get_rates(
                shipping_postal_code, shipping_city, shipping_state, shipping_country
            )
            context["shipping_rates"] = rates
            context["shipping_rate_error"] = ""
        except Exception:
            context["shipping_rate_error"] = (
                "We couldn't calculate shipping. Check your address and package "
                "measurements, or contact us for a quote."
            )
            messages.error(request, context["shipping_rate_error"])
            return render(request, "checkout.html", context)

        selected_rate_id = request.POST.get("shipping_rate_id", "").strip()
        if action == "get_rates" or not selected_rate_id:
            if not rates:
                context["shipping_rate_error"] = (
                    "No shipping services were returned for this destination."
                )
            return render(request, "checkout.html", context)

        # Validate the selected rate against fresh server-side rates.
        selected_rate = next(
            (rate for rate in rates if rate["object_id"] == selected_rate_id), None
        )
        if selected_rate is None:
            messages.error(
                request,
                "Please select a valid shipping option. Rates have been refreshed."
            )
            return render(request, "checkout.html", context)

        shipping_cost = selected_rate["amount"]
        total = subtotal + shipping_cost

        context.update({
            "shipping_cost": shipping_cost,
            "total": total,
            "grand_total": total,
            "selected_shipping_rate": selected_rate,
        })

        if action != "place_order":
            return render(request, "checkout.html", context)

        try:
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
                    notes=(
                        (notes + "\n") if notes else ""
                    ) + (
                        "Shipping: {} - {} (Shippo rate ID: {})".format(
                            selected_rate["provider"],
                            selected_rate["service"],
                            selected_rate["object_id"],
                        )
                    ),
                )
                for item in items:
                    product = item["product"]
                    quantity = item["quantity"]
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        quantity=quantity,
                        unit_price=product.price,
                        total_price=product.price * quantity,
                        currency="USD",
                    )
        except Exception:
            messages.error(
                request,
                "We could not save your order. Your cart has been kept. Please try again."
            )
            return render(request, "checkout.html", context)

        request.session["cart"] = {}
        request.session["last_order_id"] = order.pk
        request.session.modified = True
        messages.success(request, f"Your order #{order.pk} has been placed successfully.")
        return redirect("order_success", order_id=order.pk)

    return render(request, "checkout.html", context)

def order_success(request, order_id):
    from django.shortcuts import render, get_object_or_404
    from .models import Order

    order = get_object_or_404(Order, pk=order_id)
    return render(request, "order_success.html", {"order": order})

