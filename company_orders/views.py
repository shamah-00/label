from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from products.models import Product
from .forms import CompanyOrderRequestForm
from .models import CompanyOrderRequest, CompanyOrderItem, KnownCompany


MAX_ITEMS_PER_REQUEST = 25
CUSTOM_PRODUCT = "CUSTOM"


@require_http_methods(["GET", "POST"])
def company_order(request):
    products = Product.objects.filter(is_available=True).order_by("name")
    product_errors = {}
    submitted_items = []

    if request.method == "GET":
        session_cart = request.session.get("cart", {})
        if isinstance(session_cart, dict):
            for product_id, raw_quantity in session_cart.items():
                try:
                    product = products.get(pk=int(product_id))
                    quantity = max(1, min(1000000, int(raw_quantity)))
                except (TypeError, ValueError, Product.DoesNotExist):
                    continue

                catalog_price = getattr(product, "discount_price", None)
                if catalog_price is None:
                    catalog_price = getattr(product, "price", "")

                submitted_items.append({
                    "index": len(submitted_items),
                    "product_id": str(product.pk),
                    "quantity": str(quantity),
                    "price": str(catalog_price) if catalog_price else "",
                    "custom_description": "",
                    "error": "",
                })

    form = CompanyOrderRequestForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            item_count = int(request.POST.get("item_count", "0"))
        except (TypeError, ValueError):
            item_count = 0

        parsed_items = []

        if item_count < 1 or item_count > MAX_ITEMS_PER_REQUEST:
            product_errors["general"] = (
                f"Add between 1 and {MAX_ITEMS_PER_REQUEST} products."
            )
        else:
            for index in range(item_count):
                raw_product = request.POST.get(f"product_{index}", "").strip()
                raw_quantity = request.POST.get(f"quantity_{index}", "").strip()
                raw_price = request.POST.get(f"price_{index}", "").strip()
                custom_description = request.POST.get(
                    f"custom_description_{index}", ""
                ).strip()

                product = None

                if raw_product == CUSTOM_PRODUCT:
                    if not custom_description:
                        product_errors[index] = (
                            "Describe the custom product you need."
                        )
                        continue
                    if len(custom_description) > 10000:
                        product_errors[index] = (
                            "The custom product description is too long."
                        )
                        continue
                else:
                    try:
                        product_id = int(raw_product)
                        product = products.get(pk=product_id)
                    except (TypeError, ValueError, Product.DoesNotExist):
                        product_errors[index] = (
                            "Choose a valid available product or CUSTOM."
                        )
                        continue

                try:
                    quantity = int(raw_quantity)
                    if quantity < 1 or quantity > 1000000:
                        raise ValueError
                except (TypeError, ValueError):
                    product_errors[index] = (
                        "Enter a whole quantity greater than zero."
                    )
                    continue

                try:
                    price = Decimal(raw_price)
                    if (
                        not price.is_finite()
                        or price <= 0
                        or price > Decimal("9999999999.99")
                    ):
                        raise InvalidOperation
                    price = price.quantize(Decimal("0.01"))
                except (InvalidOperation, TypeError, ValueError):
                    product_errors[index] = (
                        "Enter a valid requested unit price in USD."
                    )
                    continue

                parsed_items.append({
                    "product": product,
                    "quantity": quantity,
                    "price": price,
                    "custom_description": (
                        custom_description if raw_product == CUSTOM_PRODUCT else ""
                    ),
                    "product_id": raw_product,
                })

            if not product_errors and not parsed_items:
                product_errors["general"] = "Add at least one valid product."

        if not product_errors:
            company_name = form.cleaned_data["company_name"]
            company = KnownCompany.objects.filter(
                is_active=True,
                name__iexact=company_name,
            ).first()

            first = parsed_items[0]

            with transaction.atomic():
                order = CompanyOrderRequest.objects.create(
                    company=company,
                    company_name=company_name,
                    contact_name=form.cleaned_data["contact_name"],
                    email=form.cleaned_data["email"],
                    phone=form.cleaned_data["phone"],
                    product=first["product"],
                    quantity=first["quantity"],
                    requested_unit_price=first["price"],
                    notes=form.cleaned_data["notes"],
                    status="pending",
                )

                CompanyOrderItem.objects.bulk_create([
                    CompanyOrderItem(
                        order_request=order,
                        product=item["product"],
                        custom_description=item["custom_description"],
                        quantity=item["quantity"],
                        requested_unit_price=item["price"],
                    )
                    for item in parsed_items
                ])

            messages.success(
                request,
                "Your company order request has been received for staff review. "
                "Requested prices are not confirmed until approved."
            )
            return redirect("company_orders:success")

    # Keep exactly the submitted rows when validation fails.
    if request.method == "POST":
        try:
            row_count = min(
                max(int(request.POST.get("item_count", "1")), 1),
                MAX_ITEMS_PER_REQUEST,
            )
        except (TypeError, ValueError):
            row_count = 1

        submitted_items = []
        for index in range(row_count):
            submitted_items.append({
                "index": index,
                "product_id": request.POST.get(f"product_{index}", ""),
                "quantity": request.POST.get(f"quantity_{index}", "1"),
                "price": request.POST.get(f"price_{index}", ""),
                "custom_description": request.POST.get(
                    f"custom_description_{index}", ""
                ),
                "error": product_errors.get(index, ""),
            })

    if not submitted_items:
        submitted_items = [{
            "index": 0,
            "product_id": "",
            "quantity": "1",
            "price": "",
            "custom_description": "",
            "error": "",
        }]

    return render(request, "company_orders/order_form.html", {
        "form": form,
        "products": products,
        "submitted_items": submitted_items,
        "product_errors": product_errors,
        "max_items": MAX_ITEMS_PER_REQUEST,
    })


def company_order_success(request):
    return render(request, "company_orders/success.html")
