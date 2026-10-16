from pathlib import Path
import re

path = Path("staff/views.py")
source = path.read_text(encoding="utf-8")

start_match = re.search(
    r"(?m)^@staff_required[ \t]*\r?\ndef staff_quotes\s*\(request\):",
    source
)

if not start_match:
    start_match = re.search(
        r"(?m)^def staff_quotes\s*\(request\):",
        source
    )

end_match = re.search(
    r"(?m)^def boss_staff_management\s*\(",
    source
)

if not start_match or not end_match or start_match.start() >= end_match.start():
    raise RuntimeError(
        "Could not safely locate the placeholder views. "
        "No changes were made to the source file."
    )

replacement = '''
def _label_group_customer_records():
    """
    Build one customer directory from existing orders and quote requests.
    This does not create or modify database records.
    """
    from types import SimpleNamespace
    from products.models import Order, QuoteRequest

    records = {}

    def value(obj, *names):
        for name in names:
            result = getattr(obj, name, None)
            if result not in (None, ""):
                return str(result).strip()
        return ""

    def add_record(obj, source_type):
        name = value(obj, "customer_name", "full_name", "name")
        email = value(obj, "customer_email", "email").lower()
        phone = value(obj, "customer_phone", "phone", "telephone")
        address = value(obj, "shipping_address", "address")

        if not (name or email or phone):
            return

        key = email or phone or name.casefold()
        if not key:
            return

        if key not in records:
            records[key] = {
                "name": name or email or phone,
                "email": email,
                "phone": phone,
                "address": address,
                "total_orders": 0,
                "total_quotes": 0,
                "sources": set(),
            }

        customer = records[key]

        if name and not customer["name"]:
            customer["name"] = name
        if email and not customer["email"]:
            customer["email"] = email
        if phone and not customer["phone"]:
            customer["phone"] = phone
        if address and not customer["address"]:
            customer["address"] = address

        customer["sources"].add(source_type)

        if source_type == "order":
            customer["total_orders"] += 1
        elif source_type == "quote":
            customer["total_quotes"] += 1

    for order in Order.objects.all().iterator():
        add_record(order, "order")

    for quote in QuoteRequest.objects.all().iterator():
        add_record(quote, "quote")

    customers = []

    for item in records.values():
        item["sources"] = ", ".join(sorted(item["sources"]))
        customers.append(SimpleNamespace(
            name=item["name"],
            full_name=item["name"],
            customer_name=item["name"],
            email=item["email"],
            customer_email=item["email"],
            phone=item["phone"],
            customer_phone=item["phone"],
            address=item["address"],
            total_orders=item["total_orders"],
            total_quotes=item["total_quotes"],
            sources=item["sources"],
        ))

    return sorted(customers, key=lambda customer: customer.name.lower())


@staff_required
def staff_quotes(request):
    from django.db.models import Q
    from products.models import QuoteRequest

    quotes = QuoteRequest.objects.all().order_by("-pk")
    search = request.GET.get("search", "").strip()

    if search:
        filters = Q()
        field_names = {
            field.name for field in QuoteRequest._meta.get_fields()
            if getattr(field, "concrete", False)
            and not getattr(field, "many_to_many", False)
        }

        for field in ("customer_name", "customer_email", "customer_phone",
                      "company_name", "status"):
            if field in field_names:
                filters |= Q(**{field + "__icontains": search})

        if filters:
            quotes = quotes.filter(filters)

    return render(request, "staff/quotes.html", {
        "quotes": quotes,
        "search_query": search,
    })


@staff_required
def staff_customers(request):
    from django.core.paginator import Paginator

    customers = _label_group_customer_records()
    search = request.GET.get("search", "").strip()

    if search:
        search_lower = search.lower()
        customers = [
            customer for customer in customers
            if search_lower in customer.name.lower()
            or search_lower in customer.email.lower()
            or search_lower in customer.phone.lower()
        ]

    paginator = Paginator(customers, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "staff/customers.html", {
        "customers": page_obj.object_list,
        "page_obj": page_obj,
        "search_query": search,
        "total_customers": len(customers),
    })


@staff_required
def staff_quote_detail(request, pk):
    from django.shortcuts import get_object_or_404
    from products.models import QuoteRequest

    quote = get_object_or_404(QuoteRequest, pk=pk)

    if request.method == "POST":
        from django.contrib import messages

        field_names = {
            field.name for field in QuoteRequest._meta.get_fields()
            if getattr(field, "concrete", False)
        }

        new_status = request.POST.get("status", "").strip()
        if new_status and "status" in field_names:
            valid_statuses = {
                str(choice[0])
                for choice in getattr(
                    QuoteRequest, "STATUS_CHOICES", ()
                )
            }

            if not valid_statuses or new_status in valid_statuses:
                quote.status = new_status
                quote.save(update_fields=["status"])
                messages.success(request, "Quote status updated.")
            else:
                messages.error(request, "Please select a valid quote status.")

        return redirect("staff_quote_detail", pk=quote.pk)

    return render(request, "staff/quote_detail.html", {
        "quote": quote,
        "quote_id": quote.pk,
    })


'''

updated = source[:start_match.start()] + replacement + source[end_match.start():]

# Save only after all replacement checks have passed.
path.write_text(updated, encoding="utf-8", newline="\n")
print("Updated staff/views.py successfully.")
