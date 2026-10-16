import inspect
from django.urls import resolve
from products.models import Product, Order, QuoteRequest

print("\n========== DATABASE COUNTS ==========")
print("Products:", Product.objects.count())
print("Available products:", Product.objects.filter(is_available=True).count())
print("Orders:", Order.objects.count())
print("Quote requests:", QuoteRequest.objects.count())

print("\n========== QUOTE STATUSES ==========")
for status in QuoteRequest.objects.values_list("status", flat=True).distinct():
    print(f"{status}: {QuoteRequest.objects.filter(status=status).count()}")

print("\n========== STAFF COUNTS ==========")
try:
    from staff.models import StaffProfile, StaffActivityLog
    print("Staff profiles:", StaffProfile.objects.count())
    print("Approved staff:", StaffProfile.objects.filter(status="approved").count())
    print("Pending staff:", StaffProfile.objects.filter(status="pending").count())
    print("Activity records:", StaffActivityLog.objects.count())
except Exception as exc:
    print("Staff counts unavailable:", exc)

print("\n========== ACTIVE DASHBOARD VIEW ==========")
try:
    match = resolve("/staff/")
    view = match.func
    print("URL name:", match.url_name)
    print("View:", view.__module__, view.__name__)
    print("\nView source:")
    print(inspect.getsource(view))
except Exception as exc:
    print("Dashboard inspection failed:", repr(exc))

print("\n========== DASHBOARD TEMPLATE ==========")
from django.template.loader import get_template
try:
    template = get_template("staff/dashboard.html")
    print("Template:", template.origin.name)
except Exception as exc:
    print("Template error:", repr(exc))
