from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from products.models import (
    Product,
    Order,
    QuoteRequest,
    CollectionCalendarStickerOrder,
)

from .forms import (
    ProductForm,
    StaffRegistrationForm,
    OwnerStaffForm,
)

from .models import StaffProfile, StaffActivityLog


def get_staff_profile(user):
    try:
        return StaffProfile.objects.get(user=user)
    except StaffProfile.DoesNotExist:
        return None


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_staff_activity(request, staff_profile, action, description, object_name=""):
    if not staff_profile:
        return

    StaffActivityLog.objects.create(
        staff=staff_profile,
        action=action,
        description=description,
        ip_address=get_client_ip(request),
    )


def staff_required(view_func):
    @login_required(login_url="staff_login")
    def wrapper(request, *args, **kwargs):
        if not request.user.is_active:
            messages.error(
                request,
                "Your staff account has been deactivated or removed. Please contact the Boss.",
            )
            logout(request)
            return redirect("staff_login")

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        profile = get_staff_profile(request.user)

        if not profile:
            messages.error(request, "You do not have a staff profile.")
            logout(request)
            return redirect("staff_login")

        if not profile.approved or profile.status != "approved":
            messages.error(
                request,
                "Your staff account has not been approved yet.",
            )
            logout(request)
            return redirect("staff_login")

        return view_func(request, *args, **kwargs)

    return wrapper


def boss_required(view_func):
    @login_required(login_url="staff_login")
    def wrapper(request, *args, **kwargs):
        if not request.user.is_active:
            messages.error(request, "Your account is inactive.")
            logout(request)
            return redirect("staff_login")

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        profile = get_staff_profile(request.user)

        if not profile:
            messages.error(request, "Staff profile not found.")
            return redirect("staff_dashboard")

        if not profile.approved or profile.status != "approved":
            messages.error(request, "Your account is not approved.")
            return redirect("staff_dashboard")

        if profile.role != "manager":
            messages.error(
                request,
                "Boss access is required for this section.",
            )
            return redirect("staff_dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper


@staff_required
def staff_dashboard(request):
    profile = get_staff_profile(request.user)

    products_count = Product.objects.count()
    available_products_count = Product.objects.filter(
        is_available=True
    ).count()

    orders_count = Order.objects.count()
    quotes_count = QuoteRequest.objects.count()

    new_quotes_count = QuoteRequest.objects.filter(
        status="new"
    ).count()

    reviewing_quotes_count = QuoteRequest.objects.filter(
        status="reviewing"
    ).count()

    quoted_count = QuoteRequest.objects.filter(
        status="quoted"
    ).count()

    approved_quotes_count = QuoteRequest.objects.filter(
        status="approved"
    ).count()

    in_production_count = QuoteRequest.objects.filter(
        status="in_production"
    ).count()

    completed_quotes_count = QuoteRequest.objects.filter(
        status="completed"
    ).count()

    if profile:
        profile.last_activity = timezone.now()
        profile.save(update_fields=["last_activity"])

    recent_quotes = QuoteRequest.objects.order_by("-created_at")[:8]
    recent_activity = StaffActivityLog.objects.select_related(
        "staff", "staff__user"
    ).order_by("-id")[:8]

    approved_staff_count = StaffProfile.objects.filter(
        approved=True, status="approved"
    ).count()
    pending_staff_count = StaffProfile.objects.exclude(
        approved=True, status="approved"
    ).count()

    context = {
        "total_products": products_count,
        "available_products": available_products_count,
        "total_orders": orders_count,
        "total_quotes": quotes_count,
        "new_quotes": new_quotes_count,
        "reviewing_quotes": reviewing_quotes_count,
        "quoted_quotes": quoted_count,
        "approved_quotes": approved_quotes_count,
        "production_quotes": in_production_count,
        "completed_quotes": completed_quotes_count,
        "approved_staff": approved_staff_count,
        "pending_staff": pending_staff_count,
        "recent_quotes": recent_quotes,
        "recent_activity": recent_activity,
        "profile": profile,
        "products_count": products_count,
        "available_products_count": available_products_count,
        "orders_count": orders_count,
        "quotes_count": quotes_count,
        "new_quotes_count": new_quotes_count,
        "reviewing_quotes_count": reviewing_quotes_count,
        "quoted_count": quoted_count,
        "approved_quotes_count": approved_quotes_count,
        "in_production_count": in_production_count,
        "completed_quotes_count": completed_quotes_count,
    }

    return render(
        request,
        "staff/dashboard.html",
        context,
    )


@staff_required
def staff_products(request):
    products = Product.objects.all().order_by("-created_at")

    return render(
        request,
        "staff/products.html",
        {
            "products": products,
        },
    )


@staff_required
def staff_product_add(request):
    if request.method == "POST":
        form = ProductForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            product = form.save()

            profile = get_staff_profile(request.user)

            log_staff_activity(
                request,
                profile,
                "create",
                f"Created product: {product.name}",
                product.name,
            )

            messages.success(
                request,
                "Product created successfully.",
            )

            return redirect("staff_products")
    else:
        form = ProductForm()

    return render(
        request,
        "staff/product_form.html",
        {
            "form": form,
            "title": "Add Product",
        },
    )


@staff_required
def staff_product_edit(request, pk):
    product = get_object_or_404(
        Product,
        pk=pk,
    )

    if request.method == "POST":
        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product,
        )

        if form.is_valid():
            product = form.save()

            profile = get_staff_profile(request.user)

            log_staff_activity(
                request,
                profile,
                "update",
                f"Updated product: {product.name}",
                product.name,
            )

            messages.success(
                request,
                "Product updated successfully.",
            )

            return redirect("staff_products")
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "staff/product_form.html",
        {
            "form": form,
            "product": product,
            "title": "Edit Product",
        },
    )


@staff_required
def staff_customers(request):
    customers = (
        Order.objects
        .values(
            "customer_name",
            "customer_email",
            "customer_phone",
        )
        .distinct()
        .order_by("customer_name")
    )

    return render(
        request,
        "staff/customers.html",
        {
            "customers": customers,
        },
    )


@staff_required
def staff_orders(request):
    orders = Order.objects.all().order_by("-created_at")

    return render(
        request,
        "staff/orders.html",
        {
            "orders": orders,
        },
    )



@boss_required
def owner_create_staff(request):
    if request.method == "POST":
        form = OwnerStaffForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)

                password = form.cleaned_data.get("password1")

                if password:
                    user.set_password(password)

                user.is_active = True
                user.is_staff = True
                user.save()

                profile = StaffProfile.objects.create(
                    user=user,
                    approved=True,
                    status="approved",
                    approved_at=timezone.now(),
                )

            log_staff_activity(
                request,
                get_staff_profile(request.user),
                "create",
                f"Boss created staff account: {user.username}",
                user.username,
            )

            messages.success(
                request,
                f"Staff account for {user.username} created successfully.",
            )

            return redirect("boss_staff_management")
    else:
        form = OwnerStaffForm()

    return render(
        request,
        "staff/boss/create_staff.html",
        {
            "form": form,
        },
    )


@boss_required
@transaction.atomic
def approve_staff(request, pk):
    if request.method != "POST":
        return redirect("boss_staff_management")

    profile = get_object_or_404(
        StaffProfile,
        pk=pk,
    )

    if profile.user == request.user:
        messages.warning(
            request,
            "The Boss account cannot be changed here.",
        )
        return redirect("boss_staff_management")

    if profile.user.is_superuser:
        messages.warning(
            request,
            "A superuser account cannot be changed here.",
        )
        return redirect("boss_staff_management")

    profile.approved = True
    profile.status = "approved"
    profile.approved_at = timezone.now()
    profile.rejection_reason = ""

    profile.user.is_active = True
    profile.user.is_staff = True
    profile.user.save(
        update_fields=[
            "is_active",
            "is_staff",
        ]
    )

    profile.save()

    log_staff_activity(
        request,
        get_staff_profile(request.user),
        "approve",
        f"Approved staff member: {profile.user.username}",
        profile.user.username,
    )

    messages.success(
        request,
        f"{profile.user.username} has been approved.",
    )

    return redirect("boss_staff_management")


@boss_required
@transaction.atomic
def reject_staff(request, pk):
    if request.method != "POST":
        return redirect("boss_staff_management")

    profile = get_object_or_404(
        StaffProfile,
        pk=pk,
    )

    if profile.user == request.user:
        messages.warning(
            request,
            "The Boss account cannot be rejected.",
        )
        return redirect("boss_staff_management")

    if profile.user.is_superuser:
        messages.warning(
            request,
            "A superuser account cannot be rejected.",
        )
        return redirect("boss_staff_management")

    reason = request.POST.get(
        "rejection_reason",
        "Rejected by Boss",
    ).strip()

    profile.approved = False
    profile.status = "rejected"
    profile.rejection_reason = reason

    profile.user.is_active = False
    profile.user.is_staff = False
    profile.user.save(
        update_fields=[
            "is_active",
            "is_staff",
        ]
    )

    profile.save()

    log_staff_activity(
        request,
        get_staff_profile(request.user),
        "reject",
        f"Rejected staff member: {profile.user.username}",
        profile.user.username,
    )

    messages.success(
        request,
        f"{profile.user.username} has been rejected.",
    )

    return redirect("boss_staff_management")


@boss_required
@transaction.atomic
def deactivate_staff(request, pk):
    if request.method != "POST":
        return redirect("boss_staff_management")

    profile = get_object_or_404(
        StaffProfile,
        pk=pk,
    )

    if profile.user == request.user:
        messages.warning(
            request,
            "The Boss account cannot be deactivated.",
        )
        return redirect("boss_staff_management")

    if profile.user.is_superuser:
        messages.warning(
            request,
            "A superuser account cannot be deactivated.",
        )
        return redirect("boss_staff_management")

    if profile.status != "approved" or not profile.approved:
        messages.warning(
            request,
            "Only approved staff members can be deactivated.",
        )
        return redirect("boss_staff_management")

    if not profile.user.is_active:
        messages.warning(
            request,
            f"{profile.user.username} is already deactivated.",
        )
        return redirect("boss_staff_management")

    profile.user.is_active = False
    profile.user.save(
        update_fields=["is_active"]
    )

    log_staff_activity(
        request,
        get_staff_profile(request.user),
        "deactivate",
        f"Deactivated staff member: {profile.user.username}",
        profile.user.username,
    )

    messages.success(
        request,
        f"{profile.user.username} has been deactivated.",
    )

    return redirect("boss_staff_management")


@boss_required
@transaction.atomic
def reactivate_staff(request, pk):
    if request.method != "POST":
        return redirect("boss_staff_management")

    profile = get_object_or_404(
        StaffProfile,
        pk=pk,
    )

    if profile.user == request.user:
        messages.warning(
            request,
            "The Boss account does not need reactivation.",
        )
        return redirect("boss_staff_management")

    if profile.user.is_superuser:
        messages.warning(
            request,
            "A superuser account cannot be changed here.",
        )
        return redirect("boss_staff_management")

    if profile.status != "approved" or not profile.approved:
        messages.warning(
            request,
            "This account is not an approved staff account. Approve it again instead.",
        )
        return redirect("boss_staff_management")

    if profile.user.is_active:
        messages.warning(
            request,
            f"{profile.user.username} is already active.",
        )
        return redirect("boss_staff_management")

    profile.user.is_active = True
    profile.user.is_staff = True
    profile.user.save(
        update_fields=[
            "is_active",
            "is_staff",
        ]
    )

    log_staff_activity(
        request,
        get_staff_profile(request.user),
        "reactivate",
        f"Reactivated staff member: {profile.user.username}",
        profile.user.username,
    )

    messages.success(
        request,
        f"{profile.user.username} has been reactivated.",
    )

    return redirect("boss_staff_management")


@boss_required
@transaction.atomic
def remove_staff(request, pk):
    if request.method != "POST":
        return redirect("boss_staff_management")

    profile = get_object_or_404(
        StaffProfile,
        pk=pk,
    )

    if profile.user == request.user:
        messages.warning(
            request,
            "The Boss account cannot be removed.",
        )
        return redirect("boss_staff_management")

    if profile.user.is_superuser:
        messages.warning(
            request,
            "A superuser account cannot be removed.",
        )
        return redirect("boss_staff_management")

    profile.status = "rejected"
    profile.approved = False
    profile.rejection_reason = "Removed by Boss"

    profile.user.is_active = False
    profile.user.is_staff = False
    profile.user.save(
        update_fields=[
            "is_active",
            "is_staff",
        ]
    )

    profile.save()

    log_staff_activity(
        request,
        get_staff_profile(request.user),
        "remove",
        f"Removed staff member: {profile.user.username}",
        profile.user.username,
    )

    messages.success(
        request,
        f"{profile.user.username} has been removed from the staff system.",
    )

    return redirect("boss_staff_management")


@boss_required
def staff_activity_log(request):
    activities = (
        StaffActivityLog.objects
        .select_related(
            "staff",
            "staff__user",
        )
        .order_by("-created_at")
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    action = request.GET.get(
        "action",
        "",
    ).strip()

    if search:
        activities = activities.filter(
            description__icontains=search
        )

    if action:
        activities = activities.filter(
            action=action
        )

    log_staff_activity(
        request,
        get_staff_profile(request.user),
        "page_view",
        "Boss viewed the staff activity log.",
        "Activity Log",
    )

    return render(
        request,
        "staff/boss/activity.html",
        {
            "activities": activities,
            "search_query": search,
            "selected_action": action,
            "action_choices": StaffActivityLog.ACTION_CHOICES,
        },
    )


@staff_required
def staff_calendar_orders(request):
    from django.db.models import Q
    from products.models import Order, CollectionCalendarStickerOrder

    search = request.GET.get("search", "").strip()
    orders = Order.objects.all().order_by("-created_at")
    calendar_orders = CollectionCalendarStickerOrder.objects.all().order_by("-created_at")

    if search:
        orders = orders.filter(
            Q(customer_name__icontains=search) |
            Q(customer_email__icontains=search) |
            Q(status__icontains=search)
        )
        calendar_orders = calendar_orders.filter(
            Q(name__icontains=search) |
            Q(company__icontains=search) |
            Q(email__icontains=search) |
            Q(status__icontains=search)
        )

    return render(request, "staff/calendar_orders.html", {
        "orders": orders,
        "calendar_orders": calendar_orders,
        "search": search,
    })


@staff_required
def staff_calendar_order_detail(request, pk):
    order = get_object_or_404(
        CollectionCalendarStickerOrder,
        pk=pk,
    )

    if request.method == "POST":
        status = request.POST.get("status")
        staff_notes = request.POST.get(
            "staff_notes",
            "",
        )

        if status:
            order.status = status

        if hasattr(order, "staff_notes"):
            order.staff_notes = staff_notes

        order.save()

        profile = get_staff_profile(request.user)

        log_staff_activity(
            request,
            profile,
            "update",
            f"Updated calendar sticker order #{order.pk}",
            f"Calendar Sticker Order #{order.pk}",
        )

        messages.success(
            request,
            "Calendar sticker order updated successfully.",
        )

        return redirect(
            "staff_calendar_order_detail",
            pk=order.pk,
        )

    return render(
        request,
        "staff/calendar_order_detail.html",
        {
            "order": order,
            "status_choices": getattr(
                CollectionCalendarStickerOrder,
                "STATUS_CHOICES",
                [],
            ),
        },
    )

@boss_required
def boss_site_settings(request):
    from products.models import SiteSettings

    settings_obj = SiteSettings.get_settings()

    if request.method == "POST":
        settings_obj.company_name = request.POST.get("company_name", "").strip() or "THE LABEL GROUP"
        settings_obj.tagline = request.POST.get("tagline", "").strip() or "INDUSTRIAL PRINTS & DECALS"
        settings_obj.phone = request.POST.get("phone", "").strip()
        settings_obj.email = request.POST.get("email", "").strip()
        settings_obj.address = request.POST.get("address", "").strip()
        settings_obj.whatsapp = request.POST.get("whatsapp", "").strip()
        settings_obj.facebook = request.POST.get("facebook", "").strip()
        settings_obj.instagram = request.POST.get("instagram", "").strip()
        settings_obj.tiktok = request.POST.get("tiktok", "").strip()
        settings_obj.linkedin = request.POST.get("linkedin", "").strip()
        settings_obj.youtube = request.POST.get("youtube", "").strip()
        settings_obj.save()
        messages.success(request, "Website settings updated successfully.")
        return redirect("boss_site_settings")

    return render(request, "staff/site_settings.html", {"site_settings": settings_obj})



@staff_required
def staff_product_image_delete(request, pk):
    profile = get_staff_profile(request.user)

    product = get_object_or_404(
        Product,
        pk=pk
    )

    if request.method == "POST":
        product_name = product.name

        if product.image:
            product.image.delete(save=False)
            product.image = None
            product.save()

            log_staff_activity(
                request,
                profile,
                "update",
                f"Deleted product image: {product_name}",
                f"Staff member deleted the current image for product '{product_name}'.",
            )

            messages.success(
                request,
                f"The current image for '{product_name}' was deleted successfully."
            )
        else:
            messages.info(
                request,
                f"'{product_name}' does not currently have an image."
            )

    return redirect(
        "staff_product_edit",
        pk=product.pk
    )


from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm

def staff_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                return redirect("staff_dashboard")
            else:
                form.add_error(None, "You do not have staff permissions.")
    else:
        form = AuthenticationForm()
    return render(request, "staff/login.html", {"form": form})

from django.contrib.auth import logout

def staff_logout(request):
    logout(request)
    return redirect("staff_login")

from django.contrib.auth.forms import UserCreationForm

def staff_register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.save()
            return redirect("staff_login")
    else:
        form = UserCreationForm()
    return render(request, "staff/register.html", {"form": form})

def staff_registration_success(request):
    return render(request, "staff/registration_success.html", {})

@staff_required
def staff_profile(request):
    return render(request, "staff/profile.html", {"user": request.user})


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
    from products.models import Order, QuoteRequest

    search = request.GET.get("search", "").strip()
    people = {}

    def add_person(name, email, phone, company, kind, record):
        name = (name or "").strip()
        email = (email or "").strip()
        phone = (phone or "").strip()
        company = (company or "").strip()
        key = email.casefold() if email else (
            (name.casefold(), phone) if name or phone
            else ("record", kind, record.pk)
        )
        person = people.get(key)
        if person is None:
            person = {
                "name": name or "Customer",
                "email": email,
                "phone": phone,
                "company": company,
                "orders_count": 0,
                "quotes_count": 0,
                "last_seen": getattr(record, "created_at", None),
            }
            people[key] = person
        else:
            for field, value in (
                ("name", name), ("email", email),
                ("phone", phone), ("company", company)
            ):
                if value and (not person[field] or person[field] == "Customer"):
                    person[field] = value
            created = getattr(record, "created_at", None)
            if created and (not person["last_seen"] or created > person["last_seen"]):
                person["last_seen"] = created

        person["orders_count" if kind == "order" else "quotes_count"] += 1

    for obj in Order.objects.all().order_by("-created_at"):
        add_person(
            getattr(obj, "customer_name", ""),
            getattr(obj, "customer_email", ""),
            getattr(obj, "customer_phone", ""),
            "", "order", obj
        )

    for obj in QuoteRequest.objects.all().order_by("-created_at"):
        add_person(
            getattr(obj, "customer_name", ""),
            getattr(obj, "customer_email", ""),
            getattr(obj, "customer_phone", ""),
            getattr(obj, "company_name", ""),
            "quote", obj
        )

    customers = list(people.values())
    if search:
        term = search.casefold()
        customers = [
            p for p in customers
            if any(term in str(p.get(f, "") or "").casefold()
                   for f in ("name", "email", "phone", "company"))
        ]

    customers.sort(
        key=lambda p: p["last_seen"] or datetime.min.replace(tzinfo=None),
        reverse=True
    )
    return render(request, "staff/customers.html", {
        "customers": customers,
        "total_customers": len(customers),
        "search": search,
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


def boss_staff_management(request):
    from django.contrib import messages
    from django.contrib.auth import get_user_model
    from django.db.models import Q
    from django.shortcuts import render, redirect

    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, "Boss access is required.")
        return redirect("/staff/")

    User = get_user_model()
    search = request.GET.get("search", "").strip()

    staff_members = User.objects.filter(
        is_staff=True
    ).order_by("-date_joined")

    if search:
        staff_members = staff_members.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    context = {
        "staff_members": staff_members,
        "search_query": search,
        "staff_count": User.objects.filter(is_staff=True).count(),
        "active_staff_count": User.objects.filter(
            is_staff=True,
            is_active=True
        ).count(),
    }

    return render(
        request,
        "staff/boss/staff_management.html",
        context
    )


@staff_required
def staff_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        if order.status != "completed":
            order.status = "completed"
            order.save()
        return redirect("staff_order_detail", pk=pk)
    return render(request, "staff/order_detail.html", {"order": order})
