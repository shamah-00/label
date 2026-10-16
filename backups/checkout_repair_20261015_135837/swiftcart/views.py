from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone

from products.models import Product

from .forms import ProductForm, StaffRegistrationForm
from .models import StaffProfile, StaffActivityLog


def get_client_ip(request):
    """
    Get the user's IP address.
    """

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def log_staff_activity(
    request,
    staff_profile,
    action,
    page="",
    description=""
):
    """
    Create an activity record for a staff member.
    """

    StaffActivityLog.objects.create(
        staff=staff_profile,
        action=action,
        page=page,
        description=description,
        ip_address=get_client_ip(request),
        user_agent=request.META.get(
            "HTTP_USER_AGENT",
            ""
        )
    )

    staff_profile.last_activity = timezone.now()
    staff_profile.save(
        update_fields=["last_activity"]
    )


def staff_required(view_func):

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("staff_login")

        try:

            staff_profile = StaffProfile.objects.get(
                user=request.user
            )

        except StaffProfile.DoesNotExist:

            logout(request)

            return redirect("staff_login")

        if not staff_profile.approved:

            logout(request)

            return redirect("staff_login")

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


@staff_required
def dashboard(request):

    profile = StaffProfile.objects.get(
        user=request.user
    )

    log_staff_activity(
        request,
        profile,
        "page_view",
        "Staff Dashboard",
        "Staff member accessed the dashboard."
    )

    return render(
        request,
        "staff/dashboard.html",
        {
            "profile": profile
        }
    )


@staff_required
def product_list(request):

    profile = StaffProfile.objects.get(
        user=request.user
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
            "products": products
        }
    )


@staff_required
def add_product(request):

    profile = StaffProfile.objects.get(
        user=request.user
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
                f"Created product: {product.name}"
            )

            return redirect(
                "staff_product_list"
            )

    else:

        form = ProductForm()

    log_staff_activity(
        request,
        profile,
        "page_view",
        "Add Product",
        "Staff member opened the add product page."
    )

    return render(
        request,
        "staff/products/add.html",
        {
            "form": form
        }
    )


@staff_required
def edit_product(request, product_id):

    profile = StaffProfile.objects.get(
        user=request.user
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
                f"Updated product: {product.name}"
            )

            return redirect(
                "staff_product_list"
            )

    else:

        form = ProductForm(
            instance=product
        )

    log_staff_activity(
        request,
        profile,
        "page_view",
        "Edit Product",
        f"Staff member opened product: {product.name}"
    )

    return render(
        request,
        "staff/products/edit.html",
        {
            "form": form,
            "product": product
        }
    )


def staff_register(request):

    if request.method == "POST":

        form = StaffRegistrationForm(
            request.POST
        )

        if form.is_valid():

            full_name = form.cleaned_data["full_name"]
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            role = form.cleaned_data["role"]

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            StaffProfile.objects.create(
                user=user,
                full_name=full_name,
                role=role,
                status="pending",
                approved=False
            )

            return render(
                request,
                "staff/registration_success.html"
            )

    else:

        form = StaffRegistrationForm()

    return render(
        request,
        "staff/register.html",
        {
            "form": form
        }
    )


def staff_login(request):

    if request.method == "POST":

        username = request.POST.get(
            "username"
        )

        password = request.POST.get(
            "password"
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            try:

                staff_profile = StaffProfile.objects.get(
                    user=user
                )

            except StaffProfile.DoesNotExist:

                return render(
                    request,
                    "staff/login.html",
                    {
                        "error":
                        "This account is not registered as staff."
                    }
                )

            if not staff_profile.approved:

                return render(
                    request,
                    "staff/login.html",
                    {
                        "error":
                        "Your staff account is still awaiting approval."
                    }
                )

            login(
                request,
                user
            )

            log_staff_activity(
                request,
                staff_profile,
                "login",
                "Staff Login",
                "Staff member successfully logged in."
            )

            return redirect(
                "staff_dashboard"
            )

        return render(
            request,
            "staff/login.html",
            {
                "error":
                "Invalid username or password."
            }
        )

    return render(
        request,
        "staff/login.html"
    )


@staff_required
def staff_logout(request):

    profile = StaffProfile.objects.get(
        user=request.user
    )

    log_staff_activity(
        request,
        profile,
        "logout",
        "Staff Logout",
        "Staff member logged out."
    )

    logout(request)

    return redirect(
        "staff_login"
    )


@staff_required
def staff_profile(request):

    profile = StaffProfile.objects.get(
        user=request.user
    )

    if request.method == "POST":

        profile.full_name = request.POST.get(
            "full_name",
            ""
        )

        profile.phone = request.POST.get(
            "phone",
            ""
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
            "profile": profile
        }
    )