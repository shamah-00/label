import inspect
from pathlib import Path
from django.urls import resolve
from products.models import Product, Order, QuoteRequest

report = []

def show(text=""):
    print(text)
    report.append(str(text))

show("========== REAL DATABASE COUNTS ==========")

for label, model in [
    ("Products", Product),
    ("Orders", Order),
    ("Quote requests", QuoteRequest),
]:
    try:
        show(f"{label}: {model.objects.count()}")
    except Exception as exc:
        show(f"{label}: ERROR - {exc}")

try:
    show(f"Available products: {Product.objects.filter(is_available=True).count()}")
except Exception as exc:
    show(f"Available products: ERROR - {exc}")

show("\n========== QUOTE STATUS COUNTS ==========")
try:
    for status in QuoteRequest.objects.values_list("status", flat=True).distinct():
        count = QuoteRequest.objects.filter(status=status).count()
        show(f"{status}: {count}")
except Exception as exc:
    show(f"Quote statuses: ERROR - {exc}")

show("\n========== STAFF COUNTS ==========")
try:
    from staff.models import StaffProfile, StaffActivityLog
    show(f"Staff profiles: {StaffProfile.objects.count()}")
    show(f"Approved staff: {StaffProfile.objects.filter(status='approved').count()}")
    show(f"Pending staff: {StaffProfile.objects.filter(status='pending').count()}")
    show(f"Activity records: {StaffActivityLog.objects.count()}")
except Exception as exc:
    show(f"Staff counts: ERROR - {exc}")

show("\n========== UNDERLYING DASHBOARD VIEW ==========")
try:
    match = resolve("/staff/")
    view = inspect.unwrap(match.func)
    show(f"URL name: {match.url_name}")
    show(f"Function: {view.__module__}.{view.__name__}")
    show("\n--- Actual dashboard function source ---")
    show(inspect.getsource(view))
except Exception as exc:
    show(f"Could not unwrap dashboard view: {exc!r}")

show("\n========== DASHBOARD TEMPLATE VARIABLES ==========")
try:
    template_path = Path("templates/staff/dashboard.html")
    content = template_path.read_text(encoding="utf-8")
    show(f"Template exists: {template_path.exists()}")
    show(f"Template size: {len(content)} characters")
    for name in [
        "total_products", "available_products", "total_quotes",
        "new_quotes", "reviewing_quotes", "quoted_quotes",
        "approved_quotes", "production_quotes", "completed_quotes",
        "total_orders", "approved_staff", "pending_staff",
        "recent_quotes", "recent_activity"
    ]:
        show(f"{name}: {'used' if name in content else 'not used'}")
except Exception as exc:
    show(f"Template inspection failed: {exc!r}")

Path("dashboard_diagnostic_report.txt").write_text(
    "\n".join(report), encoding="utf-8"
)
print("\nReport saved to dashboard_diagnostic_report.txt")
