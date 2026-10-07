from functools import wraps

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
return StaffProfile.objects.filter(user=user).first()

def get_client_ip(request):
forwarded = request.META.get("HTTP_X_FORWARDED_FOR")

if forwarded:
    return forwarded.split(",")[0].strip()

return request.META.get("REMOTE_ADDR")

def log_staff_activity(
request,
profile,
action,
page,
description="",
):
if not profile:
return

StaffActivityLog.objects.create(
    staff=profile,
    action=action,
    page=page,
    description=description,
    ip_address=get_client_ip(request),
    user_agent=request.META.get("HTTP_USER_AGENT", ""),
)

profile.last_activity = timezone.now()
profile.save(update_fields=["last_activity"])



def staff_required(view_func):

@wraps(view_func)
@login_required
def wrapper(request, *args, **kwargs):

    if not request.user.is_active:
        logout(request)

        messages.error(
            request,
            "This staff account has been deactivated or removed. "
            "Please contact the Boss.",
        )

        return redirect("staff_login")

    if request.user.is_superuser:
        return view_func(request, *args, **kwargs)

    if not request.user.is_staff:
        messages.error(
            request,
            "You do not have permission to access the staff area.",
        )

        return redirect("staff_login")

    profile = get_staff_profile(request.user)

    if not profile:
        messages.error(
            request,
            "Your staff profile could not be found.",
        )

        return redirect("staff_login")

    if profile.status != "approved" or not profile.approved:
        messages.error(
            request,
            "Your staff account has not been approved by the Boss.",
        )

        return redirect("staff_login")

    return view_func(request, *args, **kwargs)

return wrapper

def boss_required(view_func):

@wraps(view_func)
@login_required
def wrapper(request, *args, **kwargs):

    if not request.user.is_active:
        logout(request)
        return redirect("staff_login")

    if not request.user.is_superuser:
        messages.error(
            request,
            "Only the Boss can access this section.",
        )

        return redirect("staff_dashboard")

    return view_func(request, *args, **kwargs)

return wrapper



@staff_required
def staff_dashboard(request):

profile = get_staff_profile(request.user)

total_products = Product.objects.count()

available_products = Product.objects.filter(
    is_available=True
).count()

total_orders = Order.objects.count()

pending_orders = Order.objects.filter(
    status="pending"
).count()

total_quotes = QuoteRequest.objects.count()

pending_quotes = QuoteRequest.objects.filter(
    status="pending"
).count()

production_quotes = QuoteRequest.objects.filter(
    status="in_production"
).count()

total_calendar_orders = (
    CollectionCalendarStickerOrder.objects.count()
)

log_staff_activity(
    request,
    profile,
    "page_view",
    "Dashboard",
    "Staff member viewed the dashboard.",
)

return render(
    request,
    "staff/dashboard.html",
    {
        "profile": profile,
        "total_products": total_products,
        "available_products": available_products,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "total_quotes": total_quotes,
        "pending_quotes": pending_quotes,
        "production_quotes": production_quotes,
        "total_calendar_orders": total_calendar_orders,
    },
)



@staff_required
def staff_products(request):

profile = get_staff_profile(request.user)

products = Product.objects.all().order_by("-created_at")

log_staff_activity(
    request,
    profile,
    "page_view",
    "Products",
    "Staff member viewed the products page.",
)

return render(
    request,
    "staff/products/list.html",
    {
        "products": products,
    },
)

@staff_required
def staff_product_add(request):

profile = get_staff_profile(request.user)

if request.method == "POST":

    form = ProductForm(
        request.POST,
        request.FILES,
    )

    if form.is_valid():

        product = form.save()

        log_staff_activity(
            request,
            profile,
            "create",
            "Products",
            f"Created product: {product.name}",
        )

        messages.success(
            request,
            "Product added successfully.",
        )

        return redirect("staff_products")

else:
    form = ProductForm()

return render(
    request,
    "staff/products/add.html",
    {
        "form": form,
    },
)

@staff_required
def staff_product_edit(request, product_id):

profile = get_staff_profile(request.user)

product = get_object_or_404(
    Product,
    id=product_id,
)

if request.method == "POST":

    form = ProductForm(
        request.POST,
        request.FILES,
        instance=product,
    )

    if form.is_valid():

        product = form.save()

        log_staff_activity(
            request,
            profile,
            "update",
            "Products",
            f"Updated product: {product.name}",
        )

        messages.success(
            request,
            "Product updated successfully.",
        )

        return redirect("staff_products")

else:
    form = ProductForm(
        instance=product
    )

return render(
    request,
    "staff/products/edit.html",
    {
        "form": form,
        "product": product,
    },
)



@staff_required
def staff_customers(request):

profile = get_staff_profile(request.user)

orders = Order.objects.all().order_by("-created_at")

customers = []

seen_emails = set()

for order in orders:

    email = (order.customer_email or "").strip().lower()

    if email and email in seen_emails:
        continue

    if email:
        seen_emails.add(email)

    customers.append(order)

log_staff_activity(
    request,
    profile,
    "page_view",
    "Customers",
    "Staff member viewed the customers page.",
)

return render(
    request,
    "staff/customers/list.html",
    {
        "customers": customers,
    },
)



@staff_required
def staff_orders(request):

profile = get_staff_profile(request.user)

orders = Order.objects.all().order_by("-created_at")

log_staff_activity(
    request,
    profile,
    "page_view",
    "Orders",
    "Staff member viewed customer orders.",
)

return render(
    request,
    "staff/orders/list.html",
    {
        "orders": orders,
    },
)

@staff_required
def staff_order_detail(request, order_id):

profile = get_staff_profile(request.user)

order = get_object_or_404(
    Order,
    id=order_id,
)

log_staff_activity(
    request,
    profile,
    "page_view",
    "Order Detail",
    f"Viewed order #{order.id}.",
)

return render(
    request,
    "staff/orders/detail.html",
    {
        "order": order,
    },
)



@staff_required
def staff_quotes(request):

profile = get_staff_profile(request.user)

quotes = QuoteRequest.objects.all().order_by(
    "-created_at"
)

log_staff_activity(
    request,
    profile,
    "page_view",
    "Quotes",
    "Staff member viewed quote requests.",
)

return render(
    request,
    "staff/quotes/list.html",
    {
        "quotes": quotes,
    },
)

@staff_required
def staff_quote_detail(request, quote_id):

profile = get_staff_profile(request.user)

quote = get_object_or_404(
    QuoteRequest,
    id=quote_id,
)

if request.method == "POST":

    status = request.POST.get("status")

    staff_notes = request.POST.get(
        "staff_notes",
        "",
    )

    if status:

        valid_statuses = dict(
            QuoteRequest.STATUS_CHOICES
        )

        if status in valid_statuses:
            quote.status = status

    quote.staff_notes = staff_notes

    quote.save()

    log_staff_activity(
        request,
        profile,
        "update",
        "Quote Detail",
        f"Updated quote #{quote.id}.",
    )

    messages.success(
        request,
        "Quote updated successfully.",
    )

    return redirect(
        "staff_quote_detail",
        quote_id=quote.id,
    )

log_staff_activity(
    request,
    profile,
    "page_view",
    "Quote Detail",
    f"Viewed quote #{quote.id}.",
)

return render(
    request,
    "staff/quotes/detail.html",
    {
        "quote": quote,
    },
)



def staff_login(request):

if request.user.is_authenticated:

    if request.user.is_superuser:
        return redirect("staff_dashboard")

    if request.user.is_staff and request.user.is_active:

        profile = get_staff_profile(
            request.user
        )

        if profile and profile.status == "approved":
            return redirect("staff_dashboard")

if request.method == "POST":

    username = request.POST.get(
        "username",
        ""
    ).strip()

    password = request.POST.get(
        "password",
        ""
    )

    user = authenticate(
        request,
        username=username,
        password=password,
    )

    if user is None:

        messages.error(
            request,
            "Invalid username or password.",
        )

        return render(
            request,
            "staff/login.html",
        )

    if not user.is_active:

        messages.error(
            request,
            "This staff account has been deactivated "
            "or removed. Please contact the Boss.",
        )

        profile = get_staff_profile(user)

        if profile:

            log_staff_activity(
                request,
                profile,
                "failed_login",
                "Staff Login",
                "Login attempted on an inactive staff account.",
            )

        return render(
            request,
            "staff/login.html",
        )

    if not user.is_superuser:

        if not user.is_staff:

            messages.error(
                request,
                "This account does not have staff access.",
            )

            return render(
                request,
                "staff/login.html",
            )

        profile = get_staff_profile(user)

        if not profile:

            messages.error(
                request,
                "Your staff profile could not be found.",
            )

            return render(
                request,
                "staff/login.html",
            )

        if profile.status != "approved" or not profile.approved:

            messages.error(
                request,
                "Your account is waiting for Boss approval.",
            )

            return render(
                request,
                "staff/login.html",
            )

    login(request, user)

    profile = get_staff_profile(user)

    log_staff_activity(
        request,
        profile,
        "login",
        "Staff Login",
        f"{user.username} logged into the staff system.",
    )

    messages.success(
        request,
        f"Welcome back, {user.get_username()}.",
    )

    return redirect("staff_dashboard")

return render(
    request,
    "staff/login.html",
)



@login_required
def staff_logout(request):

profile = get_staff_profile(
    request.user
)

if profile:

    log_staff_activity(
        request,
        profile,
        "logout",
        "Staff Logout",
        f"{request.user.username} logged out.",
    )

logout(request)

messages.success(
    request,
    "You have been logged out successfully.",
)

return redirect("staff_login")



@staff_required
def staff_profile(request):

profile = get_staff_profile(
    request.user
)

if not profile:

    messages.error(
        request,
        "Staff profile not found.",
    )

    return redirect(
        "staff_dashboard"
    )

if request.method == "POST":

    full_name = request.POST.get(
        "full_name",
        "",
    ).strip()

    phone = request.POST.get(
        "phone",
        "",
    ).strip()

    if full_name:
        profile.full_name = full_name

    profile.phone = phone

    if request.FILES.get(
        "profile_picture"
    ):
        profile.profile_picture = request.FILES[
            "profile_picture"
        ]

    profile.save()

    log_staff_activity(
        request,
        profile,
        "update",
        "Profile",
        "Staff member updated their profile.",
    )

    messages.success(
        request,
        "Your profile has been updated successfully.",
    )

    return redirect(
        "staff_profile"
    )

log_staff_activity(
    request,
    profile,
    "page_view",
    "Profile",
    "Staff member viewed their profile.",
)

return render(
    request,
    "staff/profile.html",
    {
        "profile": profile,
    },
)



def staff_register(request):

if request.user.is_authenticated:

    return redirect(
        "staff_dashboard"
    )

if request.method == "POST":

    form = StaffRegistrationForm(
        request.POST,
        request.FILES,
    )

    if form.is_valid():

        user = form.save()

        profile = get_staff_profile(
            user
        )

        if profile:

            profile.status = "pending"
            profile.approved = False

            if request.FILES.get(
                "profile_picture"
            ):
                profile.profile_picture = request.FILES[
                    "profile_picture"
                ]

            profile.save()

        messages.success(
            request,
            "Your staff account has been created. "
            "Please wait for the Boss to approve your account.",
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

boss_profile = get_staff_profile(
    request.user
)

staff_members = (
    StaffProfile.objects
    .select_related("user")
    .all()
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

active_staff = approved_staff.filter(
    user__is_active=True
)

deactivated_staff = approved_staff.filter(
    user__is_active=False
)

removed_staff = staff_members.filter(
    status="rejected"
)

log_staff_activity(
    request,
    boss_profile,
    "page_view",
    "Staff Management",
    "Boss viewed staff management.",
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

boss_profile = get_staff_profile(
    request.user
)

if request.method == "POST":

    form = OwnerStaffForm(
        request.POST,
        request.FILES,
    )

    if form.is_valid():

        with transaction.atomic():

            user = form.save()

            profile = get_staff_profile(
                user
            )

            if profile:

                profile.status = "approved"
                profile.approved = True
                profile.approved_at = timezone.now()

                if request.FILES.get(
                    "profile_picture"
                ):
                    profile.profile_picture = request.FILES[
                        "profile_picture"
                    ]

                profile.save()

            user.is_staff = True
            user.is_active = True
            user.save(
                update_fields=[
                    "is_staff",
                    "is_active",
                ]
            )

        log_staff_activity(
            request,
            boss_profile,
            "create",
            "Staff Management",
            f"Boss created staff account: {user.username}.",
        )

        messages.success(
            request,
            f"Staff account for {user.username} was created successfully.",
        )

        return redirect(
            "boss_staff_management"
        )

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
def approve_staff(request, staff_id):

boss_profile = get_staff_profile(
    request.user
)

if request.method != "POST":

    messages.error(
        request,
        "Invalid request.",
    )

    return redirect(
        "boss_staff_management"
    )

profile = get_object_or_404(
    StaffProfile.objects.select_related("user"),
    id=staff_id,
)

user = profile.user

if user == request.user:

    messages.error(
        request,
        "You cannot change your own Boss account.",
    )

    return redirect(
        "boss_staff_management"
    )

if user.is_superuser:

    messages.error(
        request,
        "A Boss account cannot be changed from this page.",
    )

    return redirect(
        "boss_staff_management"
    )

profile.status = "approved"
profile.approved = True
profile.approved_at = timezone.now()
profile.rejection_reason = ""

profile.save()

user.is_active = True
user.is_staff = True

user.save(
    update_fields=[
        "is_active",
        "is_staff",
    ]
)

log_staff_activity(
    request,
    boss_profile,
    "approve",
    "Staff Management",
    f"Boss approved staff member: {user.username}.",
)

messages.success(
    request,
    f"{user.username} has been approved successfully.",
)

return redirect(
    "boss_staff_management"
)



@boss_required
def reject_staff(request, staff_id):

boss_profile = get_staff_profile(
    request.user
)

if request.method != "POST":

    messages.error(
        request,
        "Invalid request.",
    )

    return redirect(
        "boss_staff_management"
    )

profile = get_object_or_404(
    StaffProfile.objects.select_related("user"),
    id=staff_id,
)

user = profile.user

if user == request.user:

    messages.error(
        request,
        "You cannot reject your own Boss account.",
    )

    return redirect(
        "boss_staff_management"
    )

if user.is_superuser:

    messages.error(
        request,
        "A Boss account cannot be rejected.",
    )

    return redirect(
        "boss_staff_management"
    )

reason = request.POST.get(
    "rejection_reason",
    "Rejected by Boss",
).strip()

profile.status = "rejected"
profile.approved = False
profile.rejection_reason = reason

profile.save()

user.is_active = False
user.is_staff = False

user.save(
    update_fields=[
        "is_active",
        "is_staff",
    ]
)

log_staff_activity(
    request,
    boss_profile,
    "reject",
    "Staff Management",
    f"Boss rejected staff member: {user.username}. "
    f"Reason: {reason}",
)

messages.success(
    request,
    f"{user.username}'s staff application has been rejected.",
)

return redirect(
    "boss_staff_management"
)



@boss_required
def deactivate_staff(request, staff_id):

boss_profile = get_staff_profile(
    request.user
)

if request.method != "POST":

    messages.error(
        request,
        "Invalid request.",
    )

    return redirect(
        "boss_staff_management"
    )

profile = get_object_or_404(
    StaffProfile.objects.select_related("user"),
    id=staff_id,
)

user = profile.user

if user == request.user:

    messages.error(
        request,
        "You cannot deactivate your own Boss account.",
    )

    return redirect(
        "boss_staff_management"
    )

if user.is_superuser:

    messages.error(
        request,
        "A Boss account cannot be deactivated.",
    )

    return redirect(
        "boss_staff_management"
    )

if profile.status != "approved":

    messages.error(
        request,
        "Only approved staff members can be deactivated.",
    )

    return redirect(
        "boss_staff_management"
    )

if not user.is_active:

    messages.warning(
        request,
        f"{user.username} is already deactivated.",
    )

    return redirect(
        "boss_staff_management"
    )

user.is_active = False

user.save(
    update_fields=[
        "is_active",
    ]
)

log_staff_activity(
    request,
    boss_profile,
    "deactivate",
    "Staff Management",
    f"Boss deactivated staff member: {user.username}.",
)

messages.success(
    request,
    f"{user.username} has been deactivated.",
)

return redirect(
    "boss_staff_management"
)



@boss_required
def reactivate_staff(request, staff_id):

boss_profile = get_staff_profile(
    request.user
)

if request.method != "POST":

    messages.error(
        request,
        "Invalid request.",
    )

    return redirect(
        "boss_staff_management"
    )

profile = get_object_or_404(
    StaffProfile.objects.select_related("user"),
    id=staff_id,
)

user = profile.user

if user == request.user:

    messages.error(
        request,
        "You cannot change your own Boss account.",
    )

    return redirect(
        "boss_staff_management"
    )

if user.is_superuser:

    messages.error(
        request,
        "A Boss account cannot be changed here.",
    )

    return redirect(
        "boss_staff_management"
    )

if profile.status != "approved":

    messages.error(
        request,
        "This staff member must be approved again before "
        "their account can be reactivated.",
    )

    return redirect(
        "boss_staff_management"
    )

if user.is_active:

    messages.warning(
        request,
        f"{user.username} is already active.",
    )

    return redirect(
        "boss_staff_management"
    )

user.is_active = True
user.is_staff = True

user.save(
    update_fields=[
        "is_active",
        "is_staff",
    ]
)

log_staff_activity(
    request,
    boss_profile,
    "reactivate",
    "Staff Management",
    f"Boss reactivated staff member: {user.username}.",
)

messages.success(
    request,
    f"{user.username} has been reactivated.",
)

return redirect(
    "boss_staff_management"
)



@boss_required
def remove_staff(request, staff_id):

boss_profile = get_staff_profile(
    request.user
)

if request.method != "POST":

    messages.error(
        request,
        "Invalid request.",
    )

    return redirect(
        "boss_staff_management"
    )

profile = get_object_or_404(
    StaffProfile.objects.select_related("user"),
    id=staff_id,
)

user = profile.user

if user == request.user:

    messages.error(
        request,
        "You cannot remove your own Boss account.",
    )

    return redirect(
        "boss_staff_management"
    )

if user.is_superuser:

    messages.error(
        request,
        "A Boss account cannot be removed.",
    )

    return redirect(
        "boss_staff_management"
    )

profile.status = "rejected"
profile.approved = False
profile.rejection_reason = "Removed by Boss"

profile.save()

user.is_active = False
user.is_staff = False

user.save(
    update_fields=[
        "is_active",
        "is_staff",
    ]
)

log_staff_activity(
    request,
    boss_profile,
    "remove",
    "Staff Management",
    f"Boss removed staff member: {user.username}.",
)

messages.success(
    request,
    f"{user.username} has been removed from the staff system.",
)

return redirect(
    "boss_staff_management"
)



@boss_required
def staff_activity_log(request):

profile = get_staff_profile(
    request.user
)

activities = (
    StaffActivityLog.objects
    .select_related(
        "staff",
        "staff__user",
    )
    .all()
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
    ) | activities.filter(
        staff__user__username__icontains=search
    ) | activities.filter(
        staff__full_name__icontains=search
    )

if action:

    activities = activities.filter(
        action=action
    )

log_staff_activity(
    request,
    profile,
    "page_view",
    "Activity Log",
    "Boss viewed the staff activity log.",
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

profile = get_staff_profile(
    request.user
)

orders = (
    CollectionCalendarStickerOrder.objects
    .all()
    .order_by("-created_at")
)

log_staff_activity(
    request,
    profile,
    "page_view",
    "Calendar Orders",
    "Staff member viewed collection calendar sticker orders.",
)

return render(
    request,
    "staff/calendar_orders/list.html",
    {
        "orders": orders,
    },
)

@staff_required
def staff_calendar_order_detail(
request,
order_id,
):

profile = get_staff_profile(
    request.user
)

order = get_object_or_404(
    CollectionCalendarStickerOrder,
    id=order_id,
)

if request.method == "POST":

    status = request.POST.get(
        "status"
    )

    staff_notes = request.POST.get(
        "staff_notes",
        "",
    )

    if status:

        valid_statuses = dict(
            CollectionCalendarStickerOrder.STATUS_CHOICES
        )

        if status in valid_statuses:
            order.status = status

    order.staff_notes = staff_notes

    order.save()

    log_staff_activity(
        request,
        profile,
        "update",
        "Calendar Order Detail",
        f"Updated calendar sticker order #{order.id}.",
    )

    messages.success(
        request,
        "Calendar sticker order updated successfully.",
    )

    return redirect(
        "staff_calendar_order_detail",
        order_id=order.id,
    )

log_staff_activity(
    request,
    profile,
    "page_view",
    "Calendar Order Detail",
    f"Viewed calendar sticker order #{order.id}.",
)

return render(
    request,
    "staff/calendar_orders/detail.html",
    {
        "order": order,
    },
)
