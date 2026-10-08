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
    return render(request, "products/quote_cart.html", {})

def shipping(request):
    return render(request, "products/shipping.html", {})

def custom_order(request):
    if request.method == "POST":
        QuoteRequest.objects.create(
            customer_name=request.POST.get("customer_name", "").strip(),
            company_name=request.POST.get("company_name", "").strip(),
            customer_email=request.POST.get("customer_email", "").strip(),
            customer_phone=request.POST.get("customer_phone", "").strip(),
            street_address=request.POST.get("street_address", "").strip(),
            address_continued=request.POST.get("address_continued", "").strip(),
            city=request.POST.get("city", "").strip(),
            state=request.POST.get("state", "").strip(),
            postal_code=request.POST.get("postal_code", "").strip(),
            country=request.POST.get("country", "").strip(),
            requirements=request.POST.get("requirements", "").strip(),
            uploaded_file=request.FILES.get("uploaded_file"),
        )
        return render(request, "products/quote_success.html")

    return render(request, "products/custom_order.html")








# =========================================================
# SHIPPING QUOTE DESK
# =========================================================

def shipping_quote(request):
    if request.method == "POST":
        customer_name = request.POST.get("customer_name", "").strip()
        company_name = request.POST.get("company_name", "").strip()
        customer_email = request.POST.get("customer_email", "").strip()
        customer_phone = request.POST.get("customer_phone", "").strip()

        QuoteRequest.objects.create(
            customer_name=customer_name,
            company_name=company_name,
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

        return render(request, "products/quote_success.html")

    return render(request, "products/shipping_quote.html")
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









