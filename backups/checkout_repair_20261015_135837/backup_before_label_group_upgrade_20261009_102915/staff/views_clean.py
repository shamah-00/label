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

# =====================================================

# HELPERS

# =====================================================

def get_staff_profile(user):
return StaffProfile.objects.filter(
user=user
).first()

def get_client_ip(request):
forwarded = request.META.get(
"HTTP_X_FORWARDED_FOR"
)

if forwarded:
    return forwarded.split(",")[0].strip()

return request.META.get(
    "REMOTE_ADDR"
)

def log_staff_activity(
request,
profile,
action,
page="",
description=""
):
if not profile:
return

StaffActivityLog.objects.create(
    staff=profile,
    action=action,
    page=page,
    description=description,
    ip_address=get_client_ip(request),
    user_agent=request.META.get(
        "HTTP_USER_AGENT",
        ""
    ),
)

profile.last_activity = timezone.now()

profile.save(
    update_fields=["last_activity"]
)

# =====================================================

# ACCESS CONTROL

# =====================================================

def staff_required(view_func):

@login_required
def wrapper(request, *args, **kwargs):

    if request.user.is_superuser:
        return view_func(
            request,
            *args,
            **kwargs
        )

    profile = get_staff_profile(
        request.user
    )

    if not profile:
        messages.error(
            request,
            "You do not have a staff profile."
        )

        logout(request)

        return redirect(
            "staff_login"
        )

    if (
        profile.status != "approved"
        or not profile.approved
    ):
        messages.error(
            request,
            "Your staff account has not been approved."
        )

        logout(request)

        return redirect(
            "staff_login"
        )

    return view_func(
        request,
        *args,
        **kwargs
    )

return wrapper

def boss_required(view_func):

@login_required
def wrapper(request, *args, **kwargs):

    if not request.user.is_superuser:
        messages.error(
            request,
            "Boss access is required."
        )

        return redirect(
            "staff_dashboard"
        )

    return view_func(
        request,
        *args,
        **kwargs
    )

return wrapper

# =====================================================

# DASHBOARD

# =====================================================

@staff_required
def staff_dashboard(request):

profile = get_staff_profile(
    request.user
)

total_products = Product.objects.count()

available_products = Product.objects.filter(
    is_available=True
).count()

total_quotes = QuoteRequest.objects.count()

new_quotes = QuoteRequest.objects.filter(
    status="new"
).count()

reviewing_quotes = QuoteRequest.objects.filter(
    status="reviewing"
).count()

quoted_quotes = QuoteRequest.objects.filter(
    status="quoted"
).count()

approved_quotes = QuoteRequest.objects.filter(
    status="approved"
).count()

production_quotes = QuoteRequest.objects.filter(
    status="in_production"
).count()

completed_quotes = QuoteRequest.objects.filter(
    status="completed"
).count()

total_orders = Order.objects.count()

pending_staff = StaffProfile.objects.filter(
    status="pending"
).count()

approved_staff = StaffProfile.objects.filter(
    status="approved"
).count()

recent_quotes = QuoteRequest.objects.all().order_by(
    "-created_at"
)[:5]

recent_activity = StaffActivityLog.objects.select_related(
    "staff",
    "staff__user"
).all()[:10]

log_staff_activity(
    request,
    profile,
    "page_view",
    "Dashboard",
    "Staff member viewed the dashboard."
)

return render(
    request,
    "staff/dashboard.html",
    {
        "profile": profile,
        "total_products": total_products,
        "available_products": available_products,
        "total_quotes": total_quotes,
        "new_quotes": new_quotes,
        "reviewing_quotes": reviewing_quotes,
        "quoted_quotes": quoted_quotes,
        "approved_quotes": approved_quotes,
        "production_quotes": production_quotes,
        "completed_quotes": completed_quotes,
        "total_orders": total_orders,
        "pending_staff": pending_staff,
        "approved_staff": approved_staff,
        "recent_quotes": recent_quotes,
        "recent_activity": recent_activity,
    }
)

# =====================================================

# PRODUCTS

# =====================================================

@staff_required
def staff_products(request):

profile = get_staff_profile(
    request.user
)

products = Product.objects.all().order_by(
    "-created_at"
)

log_staff_activity(
    request,
    profile,
    "page_view",
    "Products",
    "Staff member viewed the product list."
)

return render(
    request,
    "staff/products/list.html",
    {
        "products": products,
    }
)

@staff_required
def staff_product_add(request):

profile = get_staff_profile(
    request.user
)

if request.method == "POST":

    form = ProductForm(
        request.POST,
        request.FILES
    )

    if form.is_valid():

        product = form.save()

        log_staff_activity(
            request,
            profile,
            "create",
            "Products",
            f"Created product '{product.name}'."
        )

        messages.success(
            request,
            f"Product '{product.name}' was added successfully."
        )

        return redirect(
            "staff_products"
        )

else:

    form = ProductForm()

return render(
    request,
    "staff/products/add.html",
    {
        "form": form,
    }
)

@staff_required
def staff_product_edit(
request,
product_id
):

profile = get_staff_profile(
    request.user
)

product = get_object_or_404(
    Product,
    id=product_id
)

if request.method == "POST":

    form = ProductForm(
        request.POST,
        request.FILES,
        instance=product
    )

    if form.is_valid():

        product = form.save()

        log_staff_activity(
            request,
            profile,
            "update",
            "Products",
            f"Updated product '{product.name}'."
        )

        messages.success(
            request,
            f"Product '{product.name}' was updated successfully."
        )

        return redirect(
            "staff_products"
        )

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
    }
)

# =====================================================

# CUSTOMERS

# =====================================================

@staff_required
def staff_customers(request):

profile = get_staff_profile(
    request.user
)

orders = Order.objects.all().order_by(
    "-created_at"
)

customers = []

seen_emails = set()

for order in orders:

    email = order.customer_email

    if (
        email
        and email.lower() in seen_emails
    ):
        continue

    if email:
        seen_emails.add(
            email.lower()
        )

    customers.append(
        order
    )

log_staff_activity(
    request,
    profile,
    "page_view",
    "Customers",
    "Staff member viewed the customer list."
)

return render(
    request,
    "staff/customers/list.html",
    {
        "customers": customers,
    }
)

# =====================================================

# ORDERS

# =====================================================

@staff_required
def staff_orders(request):

profile = get_staff_profile(
    request.user
)

orders = Order.objects.all().order_by(
    "-created_at"
)

log_staff_activity(
    request,
    profile,
    "page_view",
    "Orders",
    "Staff member viewed the order list."
)

return render(
    request,
    "staff/orders/list.html",
    {
        "orders": orders,
    }
)

@staff_required
def staff_order_detail(
request,
order_id
):

profile = get_staff_profile(
    request.user
)

order = get_object_or_404(
    Order,
    id=order_id
)

log_staff_activity(
    request,
    profile,
    "page_view",
    "Order Detail",
    f"Staff member viewed order #{order.id}."
)

return render(
    request,
    "staff/orders/detail.html",
    {
        "order": order,
    }
)

# =====================================================

# QUOTES

# =====================================================

@staff_required
def staff_quotes(request):

profile = get_staff_profile(
    request.user
)

quotes = QuoteRequest.objects.all().order_by(
    "-created_at"
)

log_staff_activity(
    request,
    profile,
    "page_view",
    "Quote Requests",
    "Staff member viewed quote requests."
)

return render(
    request,
    "staff/quotes/list.html",
    {
        "quotes": quotes,
    }
)

@staff_required
def staff_quote_detail(
request,
quote_id
):

profile = get_staff_profile(
    request.user
)

quote = get_object_or_404(
    QuoteRequest,
    id=quote_id
)

if request.method == "POST":

    old_status = quote.status

    new_status = request.POST.get(
        "status"
    )

    staff_notes = request.POST.get(
        "staff_notes",
        ""
    )

    valid_statuses = {
        choice[0]
        for choice in QuoteRequest.STATUS_CHOICES
    }

    if (
        new_status
        and new_status in valid_statuses
    ):

        quote.status = new_status

    quote.staff_notes = staff_notes

    quote.save()

    log_staff_activity(
        request,
        profile,
        "update",
        "Quote Detail",
        (
            f"Updated quote #{quote.id}. "
            f"Status changed from "
            f"'{old_status}' to "
            f"'{quote.status}'."
        )
    )

    messages.success(
        request,
        f"Quote #{quote.id} was updated successfully."
    )

    return redirect(
        "staff_quote_detail",
        quote_id=quote.id
    )

log_staff_activity(
    request,
    profile,
    "page_view",
    "Quote Detail",
    f"Staff member viewed quote #{quote.id}."
)

return render(
    request,
    "staff/quotes/detail.html",
    {
        "quote": quote,
    }
)

# =====================================================

# STAFF LOGIN

# =====================================================

def staff_login(request):

if request.user.is_authenticated:

    profile = get_staff_profile(
        request.user
    )

    if (
        request.user.is_superuser
        or (
            profile
            and profile.status == "approved"
            and profile.approved
            and request.user.is_active
        )
    ):

        return redirect(
            "staff_dashboard"
        )

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
        password=password
    )

    if user is not None:

        profile = get_staff_profile(
            user
        )

        if user.is_superuser:

            login(
                request,
                user
            )

            if profile:

                log_staff_activity(
                    request,
                    profile,
                    "login",
                    "Staff Login",
                    "Boss logged into the staff system."
                )

            return redirect(
                "staff_dashboard"
            )

        if not user.is_active:

            messages.error(
                request,
                "This staff account has been deactivated or removed. Please contact the Boss."
            )

        elif not profile:

            messages.error(
                request,
                "No staff profile exists for this account."
            )

        elif (
            profile.status != "approved"
            or not profile.approved
        ):

            messages.error(
                request,
                "Your staff application is still awaiting approval."
            )

        else:

            login(
                request,
                user
            )

            log_staff_activity(
                request,
                profile,
                "login",
                "Staff Login",
                "Staff member logged in."
            )

            return redirect(
                "staff_dashboard"
            )

    else:

        messages.error(
            request,
            "Invalid username or password."
        )

return render(
    request,
    "staff/login.html"
)

# =====================================================

# STAFF LOGOUT

# =====================================================

def staff_logout(request):

profile = None

if request.user.is_authenticated:

    profile = get_staff_profile(
        request.user
    )

if profile:

    log_staff_activity(
        request,
        profile,
        "logout",
        "Staff Logout",
        "Staff member logged out."
    )

logout(request)

messages.success(
    request,
    "You have been logged out successfully."
)

return redirect(
    "staff_login"
)

# =====================================================

# STAFF PROFILE

# =====================================================

@staff_required
def staff_profile(request):

profile = get_staff_profile(
    request.user
)

if request.method == "POST":

    profile.full_name = request.POST.get(
        "full_name",
        profile.full_name
    )

    profile.phone = request.POST.get(
        "phone",
        profile.phone
    )

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
        "Staff Profile",
        "Staff member updated their profile."
    )

    messages.success(
        request,
        "Your profile has been updated successfully."
    )

    return redirect(
        "staff_profile"
    )

log_staff_activity(
    request,
    profile,
    "page_view",
    "Staff Profile",
    "Staff member viewed their profile."
)

return render(
    request,
    "staff/profile.html",
    {
        "profile": profile,
    }
)

# =====================================================

# STAFF REGISTRATION

# =====================================================

def staff_register(request):

if request.method == "POST":

    form = StaffRegistrationForm(
        request.POST
    )

    if form.is_valid():

        with transaction.atomic():

            user = User.objects.create_user(
                username=form.cleaned_data[
                    "username"
                ],
                email=form.cleaned_data[
                    "email"
                ],
                password=form.cleaned_data[
                    "password"
                ],
            )

            user.is_active = True
            user.is_staff = False

            user.save(
                update_fields=[
                    "is_active",
                    "is_staff",
                ]
            )

            StaffProfile.objects.create(
                user=user,
                full_name=form.cleaned_data.get(
                    "full_name",
                    ""
                ),
                phone=form.cleaned_data.get(
                    "phone",
                    ""
                ),
                role=form.cleaned_data.get(
                    "role"
                ),
                status="pending",
                approved=False,
            )

        messages.success(
            request,
            "Registration successful. Your staff application is now pending approval."
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
    }
)

def staff_registration_success(request):

return render(
    request,
    "staff/registration_success.html"
)

# =====================================================

# BOSS STAFF MANAGEMENT

# =====================================================

@boss_required
def boss_staff_management(request):

profile = get_staff_profile(
    request.user
)

staff_members = StaffProfile.objects.select_related(
    "user"
).all().order_by(
    "-joined_at"
)

pending_staff = staff_members.filter(
    status="pending",
    approved=False
)

approved_staff = staff_members.filter(
    status="approved",
    approved=True
)

deactivated_staff = approved_staff.filter(
    user__is_active=False
)

active_staff = approved_staff.filter(
    user__is_active=True
)

removed_staff = staff_members.filter(
    status="rejected"
)

log_staff_activity(
    request,
    profile,
    "page_view",
    "Staff Management",
    "Boss viewed staff management."
)

return render(
    request,
    "staff/boss/staff.html",
    {
        "staff_members": staff_members,
        "pending_staff": pending_staff,
        "approved_staff": active_staff,
        "active_staff": active_staff,
        "deactivated_staff": deactivated_staff,
        "removed_staff": removed_staff,
        "rejected_staff": removed_staff,
    }
)

@boss_required
def owner_create_staff(request):

profile = get_staff_profile(
    request.user
)

if request.method == "POST":

    form = OwnerStaffForm(
        request.POST
    )

    if form.is_valid():

        with transaction.atomic():

            user = User.objects.create_user(
                username=form.cleaned_data[
                    "username"
                ],
                email=form.cleaned_data[
                    "email"
                ],
                password=form.cleaned_data[
                    "password"
                ],
            )

            user.is_active = True
            user.is_staff = True

            user.save(
                update_fields=[
                    "is_active",
                    "is_staff",
                ]
            )

            staff_member = StaffProfile.objects.create(
                user=user,
                full_name=form.cleaned_data.get(
                    "full_name",
                    ""
                ),
                phone=form.cleaned_data.get(
                    "phone",
                    ""
                ),
                role=form.cleaned_data.get(
                    "role"
                ),
                status="approved",
                approved=True,
                approved_at=timezone.now(),
            )

        log_staff_activity(
            request,
            profile,
            "create",
            "Staff Management",
            f"Boss created staff member '{staff_member.user.username}'."
        )

        messages.success(
            request,
            f"Staff member '{staff_member.user.username}' was created successfully."
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
    }
)

@boss_required
def approve_staff(
request,
staff_id
):

if request.method != "POST":

    messages.error(
        request,
        "Please use the Approve button to approve this staff member."
    )

    return redirect(
        "boss_staff_management"
    )

profile = get_staff_profile(
    request.user
)

staff_member = get_object_or_404(
    StaffProfile,
    id=staff_id
)

if staff_member.user == request.user:

    messages.error(
        request,
        "The Boss account cannot be approved or modified through staff approval."
    )

    return redirect(
        "boss_staff_management"
    )

if staff_member.user.is_superuser:

    messages.error(
        request,
        "Superuser accounts are protected."
    )

    return redirect(
        "boss_staff_management"
    )

staff_member.status = "approved"
staff_member.approved = True
staff_member.approved_at = timezone.now()
staff_member.rejection_reason = ""

staff_member.user.is_staff = True
staff_member.user.is_active = True

staff_member.user.save(
    update_fields=[
        "is_staff",
        "is_active",
    ]
)

staff_member.save(
    update_fields=[
        "status",
        "approved",
        "approved_at",
        "rejection_reason",
    ]
)

log_staff_activity(
    request,
    profile,
    "approve",
    "Staff Management",
    f"Approved staff member '{staff_member.user.username}'."
)

messages.success(
    request,
    f"{staff_member.user.username} has been approved."
)

return redirect(
    "boss_staff_management"
)

@boss_required
def reject_staff(
request,
staff_id
):

if request.method != "POST":

    messages.error(
        request,
        "Please use the Reject button to reject this staff member."
    )

    return redirect(
        "boss_staff_management"
    )

profile = get_staff_profile(
    request.user
)

staff_member = get_object_or_404(
    StaffProfile,
    id=staff_id
)

if staff_member.user == request.user:

    messages.error(
        request,
        "The Boss account cannot reject itself."
    )

    return redirect(
        "boss_staff_management"
    )

if staff_member.user.is_superuser:

    messages.error(
        request,
        "Superuser accounts are protected."
    )

    return redirect(
        "boss_staff_management"
    )

rejection_reason = request.POST.get(
    "rejection_reason",
    ""
).strip()

staff_member.status = "rejected"
staff_member.approved = False
staff_member.rejection_reason = rejection_reason

staff_member.user.is_staff = False
staff_member.user.is_active = False

staff_member.user.save(
    update_fields=[
        "is_staff",
        "is_active",
    ]
)

staff_member.save(
    update_fields=[
        "status",
        "approved",
        "rejection_reason",
    ]
)

log_staff_activity(
    request,
    profile,
    "reject",
    "Staff Management",
    (
        f"Rejected staff member "
        f"'{staff_member.user.username}'. "
        f"Reason: "
        f"{rejection_reason or 'No reason provided.'}"
    )
)

messages.success(
    request,
    (
        f"Staff member "
        f"'{staff_member.user.username}' "
        "has been rejected successfully."
    )
)

return redirect(
    "boss_staff_management"
)

# =====================================================

# DEACTIVATE STAFF

# =====================================================

@boss_required
def deactivate_staff(
request,
staff_id
):

if request.method != "POST":

    messages.error(
        request,
        "Please use the Deactivate button to deactivate staff."
    )

    return redirect(
        "boss_staff_management"
    )

boss_profile = get_staff_profile(
    request.user
)

staff_member = get_object_or_404(
    StaffProfile,
    id=staff_id
)

if staff_member.user == request.user:

    messages.error(
        request,
        "The Boss account cannot be deactivated."
    )

    return redirect(
        "boss_staff_management"
    )

if staff_member.user.is_superuser:

    messages.error(
        request,
        "Superuser accounts are protected and cannot be deactivated."
    )

    return redirect(
        "boss_staff_management"
    )

if staff_member.status != "approved":

    messages.error(
        request,
        "Only approved staff members can be deactivated."
    )

    return redirect(
        "boss_staff_management"
    )

if not staff_member.user.is_active:

    messages.warning(
        request,
        f"{staff_member.user.username} is already deactivated."
    )

    return redirect(
        "boss_staff_management"
    )

staff_member.user.is_active = False

staff_member.user.save(
    update_fields=[
        "is_active",
    ]
)

log_staff_activity(
    request,
    boss_profile,
    "deactivate",
    "Staff Management",
    (
        f"Boss deactivated staff member "
        f"'{staff_member.user.username}'."
    )
)

messages.success(
    request,
    (
        f"Staff member "
        f"'{staff_member.user.username}' "
        "has been deactivated."
    )
)

return redirect(
    "boss_staff_management"
)

# =====================================================

# REACTIVATE STAFF

# =====================================================

@boss_required
def reactivate_staff(
request,
staff_id
):

if request.method != "POST":

    messages.error(
        request,
        "Please use the Reactivate button to reactivate staff."
    )

    return redirect(
        "boss_staff_management"
    )

boss_profile = get_staff_profile(
    request.user
)

staff_member = get_object_or_404(
    StaffProfile,
    id=staff_id
)

if staff_member.user == request.user:

    messages.error(
        request,
        "The Boss account does not need to be reactivated."
    )

    return redirect(
        "boss_staff_management"
    )

if staff_member.user.is_superuser:

    messages.error(
        request,
        "Superuser accounts are protected."
    )

    return redirect(
        "boss_staff_management"
    )

if staff_member.status != "approved":

    messages.error(
        request,
        "Only approved staff members can be reactivated. Removed or rejected staff must be approved again."
    )

    return redirect(
        "boss_staff_management"
    )

if staff_member.user.is_active:

    messages.warning(
        request,
        f"{staff_member.user.username} is already active."
    )

    return redirect(
        "boss_staff_management"
    )

staff_member.user.is_active = True
staff_member.user.is_staff = True

staff_member.user.save(
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
    (
        f"Boss reactivated staff member "
        f"'{staff_member.user.username}'."
    )
)

messages.success(
    request,
    (
        f"Staff member "
        f"'{staff_member.user.username}' "
        "has been reactivated successfully."
    )
)

return redirect(
    "boss_staff_management"
)

# =====================================================

# REMOVE STAFF

# =====================================================

@boss_required
def remove_staff(
request,
staff_id
):

if request.method != "POST":

    messages.error(
        request,
        "Please use the Remove button to remove staff."
    )

    return redirect(
        "boss_staff_management"
    )

boss_profile = get_staff_profile(
    request.user
)

staff_member = get_object_or_404(
    StaffProfile,
    id=staff_id
)

if staff_member.user == request.user:

    messages.error(
        request,
        "The Boss account cannot remove itself."
    )

    return redirect(
        "boss_staff_management"
    )

if staff_member.user.is_superuser:

    messages.error(
        request,
        "Superuser accounts are protected and cannot be removed."
    )

    return redirect(
        "boss_staff_management"
    )

username = staff_member.user.username

staff_member.status = "rejected"
staff_member.approved = False
staff_member.rejection_reason = "Removed by Boss"

staff_member.user.is_active = False
staff_member.user.is_staff = False

staff_member.user.save(
    update_fields=[
        "is_active",
        "is_staff",
    ]
)

staff_member.save(
    update_fields=[
        "status",
        "approved",
        "rejection_reason",
    ]
)

log_staff_activity(
    request,
    boss_profile,
    "remove",
    "Staff Management",
    (
        f"Boss removed staff member "
        f"'{username}'. "
        "The staff profile and activity history were preserved."
    )
)

messages.success(
    request,
    (
        f"Staff member "
        f"'{username}' "
        "has been removed from the staff system."
    )
)

return redirect(
    "boss_staff_management"
)

# =====================================================

# ACTIVITY LOG

# =====================================================

@boss_required
def staff_activity_log(request):

profile = get_staff_profile(
    request.user
)

activities = StaffActivityLog.objects.select_related(
    "staff",
    "staff__user"
).all()

search = request.GET.get(
    "search",
    ""
).strip()

action = request.GET.get(
    "action",
    ""
).strip()

if search:

    activities = (
        activities.filter(
            staff__user__username__icontains=search
        )
        | activities.filter(
            staff__full_name__icontains=search
        )
        | activities.filter(
            description__icontains=search
        )
        | activities.filter(
            page__icontains=search
        )
    )

if action:

    activities = activities.filter(
        action=action
    )

activities = activities.distinct()

log_staff_activity(
    request,
    profile,
    "page_view",
    "Activity Log",
    "Boss viewed the staff activity log."
)

return render(
    request,
    "staff/boss/activity.html",
    {
        "activities": activities,
        "search_query": search,
        "selected_action": action,
        "action_choices": StaffActivityLog.ACTION_CHOICES,
    }
)

# =====================================================

# CALENDAR STICKER ORDERS

# =====================================================

@staff_required
def staff_calendar_orders(request):

profile = get_staff_profile(
    request.user
)

orders = CollectionCalendarStickerOrder.objects.all().order_by(
    "-created_at"
)

log_staff_activity(
    request,
    profile,
    "page_view",
    "Calendar Orders",
    "Staff member viewed calendar sticker orders."
)

return render(
    request,
    "staff/calendar_orders/list.html",
    {
        "orders": orders,
    }
)

@staff_required
def staff_calendar_order_detail(
request,
order_id
):

profile = get_staff_profile(
    request.user
)

order = get_object_or_404(
    CollectionCalendarStickerOrder,
    id=order_id
)

if request.method == "POST":

    old_status = order.status

    new_status = request.POST.get(
        "status"
    )

    staff_notes = request.POST.get(
        "staff_notes",
        ""
    )

    valid_statuses = {
        choice[0]
        for choice in CollectionCalendarStickerOrder.STATUS_CHOICES
    }

    if (
        new_status
        and new_status in valid_statuses
    ):

        order.status = new_status

    order.staff_notes = staff_notes

    order.save()

    log_staff_activity(
        request,
        profile,
        "update",
        "Calendar Order Detail",
        (
            f"Updated calendar order #{order.id}. "
            f"Status changed from "
            f"'{old_status}' to "
            f"'{order.status}'."
        )
    )

    messages.success(
        request,
        f"Calendar order #{order.id} was updated successfully."
    )

    return redirect(
        "staff_calendar_order_detail",
        order_id=order.id
    )

log_staff_activity(
    request,
    profile,
    "page_view",
    "Calendar Order Detail",
    f"Staff member viewed calendar order #{order.id}."
)

return render(
    request,
    "staff/calendar_orders/detail.html",
    {
        "order": order,
    }
)
