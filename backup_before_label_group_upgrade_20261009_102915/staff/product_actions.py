from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product
from .models import StaffActivityLog, StaffProfile
from .views import staff_required


@staff_required
def delete_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    try:
        staff_profile = StaffProfile.objects.get(
            user=request.user
        )
    except StaffProfile.DoesNotExist:
        messages.error(
            request,
            "Your staff profile could not be found."
        )
        return redirect("staff_product_list")

    if request.method == "POST":

        product_name = product.name
        product_code = product.product_code

        try:

            product.delete()

            StaffActivityLog.objects.create(
                staff=staff_profile,
                action="delete",
                page="Staff Products",
                description=(
                    f"Deleted product '{product_name}' "
                    f"({product_code or 'No product code'})."
                ),
                ip_address=request.META.get(
                    "REMOTE_ADDR"
                ),
                user_agent=request.META.get(
                    "HTTP_USER_AGENT",
                    ""
                ),
            )

            messages.success(
                request,
                (
                    f"Product '{product_name}' was permanently "
                    "deleted successfully."
                )
            )

            return redirect(
                "staff_product_list"
            )

        except ProtectedError:

            messages.error(
                request,
                (
                    f"'{product_name}' cannot be permanently "
                    "deleted because it is connected to an "
                    "existing quote request. You can edit the "
                    "product and turn off "
                    "'Available on Website' instead."
                )
            )

            return redirect(
                "staff_product_list"
            )

    return render(
        request,
        "staff/products/delete.html",
        {
            "product": product,
        }
    )