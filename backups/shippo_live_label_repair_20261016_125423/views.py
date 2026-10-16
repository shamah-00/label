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
    pending_staff_count = StaffProfile.objects.filter(
        approved=False, status="pending"
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
    from collections import defaultdict
    from decimal import Decimal
    from django.db.models import Q
    from products.models import Order, QuoteRequest

    people = {}
    search = request.GET.get("search", "").strip()

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
                "total_spend": Decimal("0.00"),
                "last_seen": getattr(record, "created_at", None),
            }
            people[key] = person
        else:
            for field, value in (
                ("name", name), ("email", email),
                ("phone", phone), ("company", company),
            ):
                if value and (not person[field] or person[field] == "Customer"):
                    person[field] = value
            created = getattr(record, "created_at", None)
            if created and (
                not person["last_seen"]
                or created.timestamp() > person["last_seen"].timestamp()
            ):
                person["last_seen"] = created

        if kind == "order":
            person["orders_count"] += 1
            person["total_spend"] += record.total or Decimal("0.00")
        else:
            person["quotes_count"] += 1

    for obj in Order.objects.all().order_by("-created_at"):
        add_person(
            obj.customer_name, obj.customer_email, obj.customer_phone,
            "", "order", obj,
        )

    for obj in QuoteRequest.objects.all().order_by("-created_at"):
        add_person(
            obj.customer_name, obj.customer_email, obj.customer_phone,
            obj.company_name, "quote", obj,
        )

    customers = list(people.values())
    if search:
        needle = search.casefold()
        customers = [
            p for p in customers
            if any(needle in str(p[field] or "").casefold()
                   for field in ("name", "email", "phone", "company"))
        ]

    customers.sort(
        key=lambda p: p["last_seen"].timestamp() if p["last_seen"] else 0,
        reverse=True,
    )

    total_order_count = sum(p["orders_count"] for p in customers)
    total_quote_count = sum(p["quotes_count"] for p in customers)
    total_customer_spend = sum(
        (p["total_spend"] for p in customers), Decimal("0.00")
    )

    return render(request, "staff/customers/list.html", {
        "customers": customers,
        "total_customers": len(customers),
        "total_order_count": total_order_count,
        "total_quote_count": total_quote_count,
        "total_customer_spend": total_customer_spend,
        "search": search,
    })



@staff_required
def staff_orders(request):
    from django.db.models import Q, Sum
    from decimal import Decimal
    from products.models import Order

    all_orders = Order.objects.all().order_by("-created_at")
    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()
    status_choices = list(Order._meta.get_field("status").choices)

    if search:
        condition = (
            Q(customer_name__icontains=search)
            | Q(customer_email__icontains=search)
            | Q(customer_phone__icontains=search)
            | Q(shipping_city__icontains=search)
            | Q(shipping_country__icontains=search)
            | Q(status__icontains=search)
        )
        if search.isdigit():
            condition |= Q(pk=int(search))
        all_orders = all_orders.filter(condition)

    if status_filter and any(str(k) == status_filter for k, _ in status_choices):
        all_orders = all_orders.filter(status=status_filter)

    all_orders = all_orders.prefetch_related("items")
    status_cards = []
    for key, label in status_choices:
        status_cards.append({
            "key": key,
            "label": label,
            "count": Order.objects.filter(status=key).count(),
        })

    totals = Order.objects.aggregate(value=Sum("total"))
    total_value = totals["value"] or Decimal("0.00")
    active_statuses = [
        key for key, _ in status_choices
        if key not in ("completed", "cancelled")
    ]

    return render(request, "staff/orders/list.html", {
        "orders": all_orders,
        "search": search,
        "status_filter": status_filter,
        "status_choices": status_choices,
        "status_cards": status_cards,
        "total_orders": Order.objects.count(),
        "active_orders": Order.objects.filter(status__in=active_statuses).count(),
        "completed_orders": Order.objects.filter(status="completed").count(),
        "total_value": total_value,
    })




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
    from django.db.models import Q, Sum
    from products.models import Order, CollectionCalendarStickerOrder

    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()
    status_choices = list(
        CollectionCalendarStickerOrder._meta.get_field("status").choices
    )

    jobs = CollectionCalendarStickerOrder.objects.all().order_by(
        "-created_at", "-pk"
    )

    if search:
        condition = (
            Q(name__icontains=search)
            | Q(company__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
            | Q(title__icontains=search)
            | Q(status__icontains=search)
        )
        if search.isdigit():
            condition |= Q(pk=int(search)) | Q(calendar_year=int(search))
        jobs = jobs.filter(condition)

    if status_filter and any(str(k) == status_filter for k, _ in status_choices):
        jobs = jobs.filter(status=status_filter)

    summary = jobs.aggregate(quantity=Sum("quantity"))
    total_quantity = summary["quantity"] or 0
    years = jobs.values_list("calendar_year", flat=True).distinct().count()
    completed_keys = {"completed", "cancelled"}
    active_count = jobs.exclude(status__in=completed_keys).count()

    return render(request, "staff/calendar_orders/list.html", {
        "calendar_orders": jobs,
        "recent_orders": Order.objects.all().order_by("-created_at")[:8],
        "search": search,
        "status_filter": status_filter,
        "status_choices": status_choices,
        "total_calendar_orders": jobs.count(),
        "total_quantity": total_quantity,
        "active_calendar_orders": active_count,
        "year_count": years,
    })



@staff_required
def staff_calendar_order_detail(request, pk):
    from django.contrib import messages
    from products.models import CollectionCalendarStickerOrder

    calendar_order = get_object_or_404(CollectionCalendarStickerOrder, pk=pk)
    status_field = CollectionCalendarStickerOrder._meta.get_field("status")
    status_choices = [
        (str(key), str(label)) for key, label in status_field.choices if str(key)
    ]
    if not status_choices:
        status_choices = [
            (key, key.replace("_", " ").title())
            for key in ("pending", "reviewing", "approved", "in_production",
                        "completed", "cancelled")
        ]

    allowed_statuses = {key for key, _ in status_choices}

    if request.method == "POST":
        new_status = request.POST.get("status", "").strip()
        new_notes = request.POST.get("staff_notes", calendar_order.staff_notes)

        if new_status not in allowed_statuses:
            messages.error(request, "Please choose a valid job status.")
        else:
            changed = []
            if calendar_order.status != new_status:
                old_status = calendar_order.status
                calendar_order.status = new_status
                changed.append(f"status changed from {old_status} to {new_status}")
            if calendar_order.staff_notes != new_notes:
                calendar_order.staff_notes = new_notes
                changed.append("staff notes updated")

            if changed:
                calendar_order.save()
                profile = get_staff_profile(request.user)
                log_staff_activity(
                    request, profile, "update",
                    f"Calendar job #{calendar_order.pk}: " + "; ".join(changed),
                    f"Calendar job #{calendar_order.pk}",
                )
                messages.success(
                    request, f"Calendar job #{calendar_order.pk} has been updated."
                )
            else:
                messages.info(request, "No changes were needed.")

            return redirect(
                "staff_calendar_order_detail", pk=calendar_order.pk
            )

    return render(request, "staff/calendar_orders/detail.html", {
        "calendar_order": calendar_order,
        "status_choices": status_choices,
    })


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
    from collections import defaultdict
    from decimal import Decimal
    from django.db.models import Q
    from products.models import Order, QuoteRequest

    people = {}
    search = request.GET.get("search", "").strip()

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
                "total_spend": Decimal("0.00"),
                "last_seen": getattr(record, "created_at", None),
            }
            people[key] = person
        else:
            for field, value in (
                ("name", name), ("email", email),
                ("phone", phone), ("company", company),
            ):
                if value and (not person[field] or person[field] == "Customer"):
                    person[field] = value
            created = getattr(record, "created_at", None)
            if created and (
                not person["last_seen"]
                or created.timestamp() > person["last_seen"].timestamp()
            ):
                person["last_seen"] = created

        if kind == "order":
            person["orders_count"] += 1
            person["total_spend"] += record.total or Decimal("0.00")
        else:
            person["quotes_count"] += 1

    for obj in Order.objects.all().order_by("-created_at"):
        add_person(
            obj.customer_name, obj.customer_email, obj.customer_phone,
            "", "order", obj,
        )

    for obj in QuoteRequest.objects.all().order_by("-created_at"):
        add_person(
            obj.customer_name, obj.customer_email, obj.customer_phone,
            obj.company_name, "quote", obj,
        )

    customers = list(people.values())
    if search:
        needle = search.casefold()
        customers = [
            p for p in customers
            if any(needle in str(p[field] or "").casefold()
                   for field in ("name", "email", "phone", "company"))
        ]

    customers.sort(
        key=lambda p: p["last_seen"].timestamp() if p["last_seen"] else 0,
        reverse=True,
    )

    total_order_count = sum(p["orders_count"] for p in customers)
    total_quote_count = sum(p["quotes_count"] for p in customers)
    total_customer_spend = sum(
        (p["total_spend"] for p in customers), Decimal("0.00")
    )

    return render(request, "staff/customers/list.html", {
        "customers": customers,
        "total_customers": len(customers),
        "total_order_count": total_order_count,
        "total_quote_count": total_quote_count,
        "total_customer_spend": total_customer_spend,
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
    from django.contrib import messages
    from products.models import Order

    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        pk=pk,
    )
    status_choices = list(Order._meta.get_field("status").choices)
    allowed_statuses = {str(key) for key, _ in status_choices}

    if request.method == "POST":
        new_status = request.POST.get("status", "").strip()
        new_notes = request.POST.get("notes", order.notes)

        if new_status not in allowed_statuses:
            messages.error(request, "Please choose a valid order status.")
        else:
            changed = []
            if order.status != new_status:
                old_status = order.status
                order.status = new_status
                changed.append(f"status changed from {old_status} to {new_status}")
            if order.notes != new_notes:
                order.notes = new_notes
                changed.append("internal notes updated")

            if changed:
                order.save()
                profile = get_staff_profile(request.user)
                log_staff_activity(
                    request, profile, "update",
                    f"Order #{order.pk}: " + "; ".join(changed),
                    f"Order #{order.pk}",
                )
                messages.success(request, f"Order #{order.pk} has been updated.")
            else:
                messages.info(request, "No changes were needed.")

            return redirect("staff_order_detail", pk=order.pk)

    return render(request, "staff/orders/detail.html", {
        "order": order,
        "status_choices": status_choices,
        "items": order.items.select_related("product").all(),
        "item_count": order.items.count(),
    })


@staff_required
def staff_shipping_dashboard(request):
    import os
    import requests
    from django.conf import settings
    from django.contrib import messages
    from django.shortcuts import render, redirect
    from django.utils import timezone
    from products.models import Shipment

    if request.method == "POST":
        shipment_id = request.POST.get("shipment_id", "").strip()
        action = request.POST.get("action", "update").strip()

        shipment = Shipment.objects.select_related("order").filter(
            pk=shipment_id
        ).first()

        if not shipment:
            messages.error(request, "Shipment not found.")
            return redirect("staff_shipping_dashboard")

        if action == "purchase_label":
            live_purchase_enabled = os.environ.get(
                "THE_LABEL_GROUP_ALLOW_LIVE_SHIPPO_PURCHASES", ""
            ).strip().lower() in {"1", "true", "yes"}

            if not live_purchase_enabled:
                messages.error(
                    request,
                    "Shippo label purchasing is disabled for safety. "
                    "Verify the order, destination, parcel, rate and cost, "
                    "and explicitly enable live purchasing only when authorized."
                )
                return redirect("staff_shipping_dashboard")

            order_status = str(getattr(shipment.order, "status", "") or "").strip().lower()
            shipment_status = str(getattr(shipment, "status", "") or "").strip().lower()
            if order_status == "cancelled" or shipment_status == "cancelled":
                messages.error(request, "A shipping label cannot be purchased for a cancelled order.")
                return redirect("staff_shipping_dashboard")
            rate_id = request.POST.get("shippo_rate_id", "").strip()
            if not rate_id:
                messages.error(
                    request,
                    "Enter the valid Shippo rate ID for this order before purchasing the label."
                )
                return redirect("staff_shipping_dashboard")

            if not shipment.shippo_rate_id or rate_id != shipment.shippo_rate_id:
                messages.error(
                    request,
                    "The submitted rate does not match the rate saved for this shipment. "
                    "Refresh or recalculate shipping and save a valid rate before buying a label."
                )
                return redirect("staff_shipping_dashboard")

            if shipment.shippo_transaction_id or shipment.label_url:
                messages.error(
                    request,
                    "A Shippo transaction or label is already recorded for this shipment. "
                    "Check Shippo before attempting another purchase."
                )
                return redirect("staff_shipping_dashboard")

            token = (
                os.environ.get("SHIPPO_API_TOKEN", "").strip()
                or os.environ.get("SHIPPO_API_KEY", "").strip()
                or str(getattr(settings, "SHIPPO_API_TOKEN", "") or "").strip()
                or os.environ.get("SHIPPO_TOKEN", "").strip()
            )
            if not token:
                messages.error(
                    request,
                    "Shippo API token was not found in the server environment. Check your existing server configuration."
                )
                return redirect("staff_shipping_dashboard")

            if shipment.shippo_transaction_id and shipment.label_url:
                messages.error(
                    request,
                    "A label is already recorded for this shipment. Check the existing label before attempting another purchase."
                )
                return redirect("staff_shipping_dashboard")

            headers = {
                "Authorization": "ShippoToken " + token,
                "Content-Type": "application/json",
                "SHIPPO-API-VERSION": "2018-02-08",
            }
            payload = {
                "rate": rate_id,
                "label_file_type": "PDF",
                "async": False,
                "metadata": "The Label Group Order #" + str(shipment.order_id),
            }

            try:
                response = requests.post(
                    "https://api.goshippo.com/transactions/",
                    headers=headers,
                    json=payload,
                    timeout=45,
                )
                try:
                    result = response.json()
                except ValueError:
                    result = {}

                if response.status_code not in (200, 201):
                    detail = result.get("messages") or result.get("detail") or result.get("message")
                    if isinstance(detail, (dict, list)):
                        detail = str(detail)
                    messages.error(
                        request,
                        "Shippo did not purchase the label (HTTP "
                        + str(response.status_code)
                        + "). "
                        + str(detail or "Check the rate ID and Shippo dashboard.")
                    )
                    return redirect("staff_shipping_dashboard")

                transaction_status = str(result.get("status", "")).upper()
                label_url = result.get("label_url", "")
                transaction_id = result.get("object_id", "")
                tracking_number = result.get("tracking_number", "")
                tracking_url = result.get("tracking_url_provider", "")
                rate_data = result.get("rate") or {}
                carrier = rate_data.get("provider", "") if isinstance(rate_data, dict) else ""

                if transaction_status != "SUCCESS" or not label_url:
                    messages.error(
                        request,
                        "Shippo did not return a successful transaction with a label URL. No label is marked as purchased. Check the transaction in Shippo before retrying."
                    )
                    if transaction_id:
                        shipment.shippo_transaction_id = transaction_id
                        shipment.shippo_rate_id = rate_id
                        shipment.save(update_fields=[
                            "shippo_transaction_id",
                            "shippo_rate_id",
                            "updated_at",
                        ])
                    return redirect("staff_shipping_dashboard")

                shipment.shippo_rate_id = rate_id
                shipment.shippo_transaction_id = transaction_id
                shipment.label_url = label_url
                shipment.tracking_url = tracking_url or ""
                shipment.tracking_number = tracking_number or shipment.tracking_number
                shipment.carrier = carrier or shipment.carrier or "Shippo carrier"
                shipment.shipping_method = (
                    rate_data.get("servicelevel", {}).get("name", shipment.shipping_method)
                    if isinstance(rate_data, dict) and isinstance(rate_data.get("servicelevel"), dict)
                    else shipment.shipping_method
                )
                shipment.status = "shipped"
                if shipment.shipped_at is None:
                    shipment.shipped_at = timezone.now()
                shipment.save()

                # Keep the order in sync when its model supports this status.
                order = shipment.order
                try:
                    status_field = order._meta.get_field("status")
                    allowed_order_statuses = {
                        value for value, label in status_field.choices
                    }
                    if (
                        "shipped" in allowed_order_statuses
                        and (order.status or "").lower() != "cancelled"
                    ):
                        order.status = "shipped"
                        order.save(update_fields=["status"])
                except Exception:
                    # Do not undo a successfully saved shipment if the
                    # order model has no compatible status choices.
                    pass

                messages.success(
                    request,
                    "Shippo label purchased successfully for Order #"
                    + str(shipment.order_id)
                    + ". Open the label link to print it."
                )

            except requests.RequestException as exc:
                messages.error(
                    request,
                    "Could not reach Shippo. Check the server connection and Shippo dashboard before retrying. "
                    + str(exc)
                )

            return redirect("staff_shipping_dashboard")

        if action == "update":
            status = request.POST.get("status", "").strip()
            allowed = {choice[0] for choice in Shipment.STATUS_CHOICES}

            if status not in allowed:
                messages.error(request, "Invalid shipment status.")
                return redirect("staff_shipping_dashboard")

            from django.utils.dateparse import parse_date

            delivery_raw = request.POST.get("estimated_delivery", "").strip()
            delivery_date = parse_date(delivery_raw) if delivery_raw else None
            if delivery_raw and delivery_date is None:
                messages.error(request, "Enter a valid estimated delivery date.")
                return redirect("staff_shipping_dashboard")

            shipment.status = status
            shipment.estimated_delivery = delivery_date
            from urllib.parse import quote

            previous_tracking_number = (shipment.tracking_number or "").strip()
            shipment.tracking_number = request.POST.get(
                "tracking_number", shipment.tracking_number
            ).strip()[:200]
            shipment.carrier = request.POST.get(
                "carrier", shipment.carrier
            ).strip()[:100]

            current_tracking_number = (shipment.tracking_number or "").strip()
            carrier_key = (shipment.carrier or "").lower()

            # Keep an existing Shippo URL when the tracking number is unchanged.
            # If staff changes or clears the number, never leave a stale link.
            if current_tracking_number != previous_tracking_number:
                shipment.tracking_url = ""

            if current_tracking_number and not shipment.tracking_url:
                encoded_tracking = quote(current_tracking_number, safe="")
                if "ups" in carrier_key:
                    shipment.tracking_url = (
                        "https://www.ups.com/track?tracknum=" + encoded_tracking
                    )
                elif "fedex" in carrier_key:
                    shipment.tracking_url = (
                        "https://www.fedex.com/fedextrack/?trknbr=" + encoded_tracking
                    )
                elif "dhl" in carrier_key:
                    shipment.tracking_url = (
                        "https://www.dhl.com/global-en/home/tracking.html?tracking-id="
                        + encoded_tracking
                    )
            shipment.shipping_method = request.POST.get(
                "shipping_method", shipment.shipping_method
            ).strip()[:100]
            shipment.notes = request.POST.get("notes", shipment.notes)

            if status == "shipped" and shipment.shipped_at is None:
                shipment.shipped_at = timezone.now()
            if status == "delivered" and shipment.delivered_at is None:
                shipment.delivered_at = timezone.now()

            shipment.save()

            # Keep the order status aligned with shipment progress when supported.
            order = shipment.order
            shipment_to_order = {
                "processing": "processing",
                "packed": "packed",
                "shipped": "shipped",
                "in_transit": "shipped",
                "out_for_delivery": "shipped",
                "delivered": "completed",
                "cancelled": "cancelled",
            }
            desired_order_status = shipment_to_order.get(status)
            if desired_order_status and (order.status or "").lower() != "cancelled":
                try:
                    field = order._meta.get_field("status")
                    choices = {value for value, label in field.choices}
                    if desired_order_status in choices:
                        order.status = desired_order_status
                        order.save(update_fields=["status"])
                except Exception:
                    # Shipment changes remain saved if the order model differs.
                    pass

            messages.success(request, "Shipment details updated.")
            return redirect("staff_shipping_dashboard")

        messages.error(request, "Unknown shipping action.")
        return redirect("staff_shipping_dashboard")

    shipments = list(Shipment.objects.select_related("order").order_by("-updated_at"))

    # Display each address component once, including overlapping city/state/ZIP data.
    # Build a display-only address without repeating city, state or ZIP.
    # Original order address fields are not modified.
    for shipment in shipments:
        order = shipment.order
        address_fields = [
            getattr(order, "shipping_address", ""),
            getattr(order, "shipping_city", ""),
            getattr(order, "shipping_state", ""),
            getattr(order, "shipping_postal_code", ""),
            getattr(order, "shipping_country", ""),
        ]

        parts = []
        seen = set()

        for field in address_fields:
            text_value = " ".join(
                str(field or "").replace("\r", " ").replace("\n", " ").split()
            ).strip(" ,")

            if not text_value:
                continue

            for raw_part in text_value.split(","):
                part = " ".join(raw_part.split()).strip(" ,")
                key = " ".join(part.casefold().split())

                if not key or key in seen:
                    continue

                # Avoid appending city/state/ZIP when already included in
                # a previously displayed address component.
                already_included = any(
                    key in " ".join(existing.casefold().split())
                    or " ".join(existing.casefold().split()) in key
                    for existing in parts
                )

                if already_included:
                    continue

                seen.add(key)
                parts.append(part)

        shipment.shipping_destination = ", ".join(parts)
    return render(request, "staff/shipping/dashboard.html", {
        "shipments": shipments,
        "status_choices": Shipment.STATUS_CHOICES,
    })

