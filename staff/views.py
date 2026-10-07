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
        object_name=object_name,
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

    context = {
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


@staff_required
def staff_order_detail(request, pk):
    order = get_object_or_404(
        Order,
        pk=pk,
    )

    return render(
        request,
        "staff/order_detail.html",
        {
            "order": order,
        },
    )


@staff_required
def staff_quotes(request):
    quotes = QuoteRequest.objects.all().order_by("-created_at")

    return render(
        request,
        "staff/quotes.html",
        {
            "quotes": quotes,
        },
    )


@staff_required
def staff_quote_detail(request, pk):
    quote = get_object_or_404(
        QuoteRequest,
        pk=pk,
    )

    if request.method == "POST":
        status = request.POST.get("status")
        staff_notes = request.POST.get("staff_notes", "")

        if status:
            quote.status = status

        if hasattr(quote, "staff_notes"):
            quote.staff_notes = staff_notes

        quote.save()

        profile = get_staff_profile(request.user)

        log_staff_activity(
            request,
            profile,
            "update",
            f"Updated quote #{quote.pk}",
            f"Quote #{quote.pk}",
        )

        messages.success(
            request,
            "Quote updated successfully.",
        )

        return redirect(
            "staff_quote_detail",
            pk=quote.pk,
        )

    return render(
        request,
        "staff/quote_detail.html",
        {
            "quote": quote,
            "status_choices": getattr(
                QuoteRequest,
                "STATUS_CHOICES",
                [],
            ),
        },
    )


def staff_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("staff_dashboard")

        profile = get_staff_profile(request.user)

        if profile and profile.approved and profile.status == "approved":
            if request.user.is_active:
                return redirect("staff_dashboard")

            logout(request)

            messages.error(
                request,
                "This staff account has been deactivated or removed. Please contact the Boss.",
            )

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            if not user.is_active:
                messages.error(
                    request,
                    "This staff account has been deactivated or removed. Please contact the Boss.",
                )
                return redirect("staff_login")

            if user.is_superuser:
                login(request, user)

                log_staff_activity(
                    request,
                    None,
                    "login",
                    "Boss logged into the staff system.",
                    "Staff Login",
                )

                return redirect("staff_dashboard")

            profile = get_staff_profile(user)

            if not profile:
                messages.error(
                    request,
                    "No staff profile was found for this account.",
                )
                return redirect("staff_login")

            if not profile.approved or profile.status != "approved":
                messages.error(
                    request,
                    "Your staff account is awaiting Boss approval.",
                )
                return redirect("staff_login")

            login(request, user)

            profile.last_activity = timezone.now()
            profile.save(update_fields=["last_activity"])

            log_staff_activity(
                request,
                profile,
                "login",
                "Staff member logged into the staff system.",
                "Staff Login",
            )

            return redirect("staff_dashboard")

        messages.error(
            request,
            "Invalid username or password.",
        )

    return render(
        request,
        "staff/login.html",
    )


@login_required
def staff_logout(request):
    profile = get_staff_profile(request.user)

    if profile:
        log_staff_activity(
            request,
            profile,
            "logout",
            "Staff member logged out.",
            "Staff Logout",
        )

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully.",
    )

    return redirect("staff_login")


@staff_required
def staff_profile(request):
    profile = get_staff_profile(request.user)

    return render(
        request,
        "staff/profile.html",
        {
            "profile": profile,
        },
    )


def staff_register(request):
    if request.user.is_authenticated:
        return redirect("staff_dashboard")

    if request.method == "POST":
        form = StaffRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            password = form.cleaned_data.get("password1")

            if password:
                user.set_password(password)

            user.is_active = True
            user.is_staff = False
            user.save()

            profile = StaffProfile.objects.create(
                user=user,
                approved=False,
                status="pending",
            )

            messages.success(
                request,
                "Your staff account has been created and is waiting for Boss approval.",
            )

            return redirect(
                "staff_registration_success"
            )
    else:
        form = StaffRegistrationForm()

    return render(
        request,
        "staff/register.html",
        {
            "form": form,
        },
    )


def staff_registration_success(request):
    return render(
        request,
        "staff/registration_success.html",
    )


@boss_required
def boss_staff_management(request):
    staff_members = (
        StaffProfile.objects
        .select_related("user")
        .order_by("-joined_at")
    )

    pending_staff = staff_members.filter(
        status="pending",
        approved=False,
    )

    approved_staff = staff_members.filter(
        status="approved",
        approved=True,
    )

    deactivated_staff = approved_staff.filter(
        user__is_active=False,
    )

    active_staff = approved_staff.filter(
        user__is_active=True,
    )

    removed_staff = staff_members.filter(
        status="rejected",
    )

    return render(
        request,
        "staff/boss/staff.html",
        {
            "staff_members": staff_members,
            "pending_staff": pending_staff,
            "approved_staff": approved_staff,
            "active_staff": active_staff,
            "deactivated_staff": deactivated_staff,
            "removed_staff": removed_staff,
            "rejected_staff": removed_staff,
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
    orders = (
        CollectionCalendarStickerOrder.objects
        .all()
        .order_by("-created_at")
    )

    return render(
        request,
        "staff/calendar_orders.html",
        {
            "orders": orders,
        },
    )


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