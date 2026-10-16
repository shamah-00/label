import inspect
from pathlib import Path
from django.urls import resolve
from django.template.loader import get_template
from products.models import Product, Order, QuoteRequest

lines = []

def out(value=""):
    value = str(value)
    print(value)
    lines.append(value)

out("THE LABEL GROUP - DASHBOARD DIAGNOSTIC")
out("\nDATABASE COUNTS")

for label, model in [
    ("Products", Product),
    ("Orders", Order),
    ("Quote requests", QuoteRequest),
]:
    try:
        out(f"{label}: {model.objects.count()}")
    except Exception as exc:
        out(f"{label}: ERROR: {exc}")

try:
    out(f"Available products: {Product.objects.filter(is_available=True).count()}")
except Exception as exc:
    out(f"Available products: ERROR: {exc}")

out("\nMODEL FIELDS")
for model in (Product, Order, QuoteRequest):
    out(f"\n{model.__name__}:")
    for field in model._meta.get_fields():
        out(f"  {field.name}")

out("\nQUOTE STATUSES")
try:
    for status in QuoteRequest.objects.values_list("status", flat=True).distinct():
        out(f"{status}: {QuoteRequest.objects.filter(status=status).count()}")
except Exception as exc:
    out(f"Could not inspect quote statuses: {exc}")

out("\nSTAFF COUNTS")
try:
    from staff.models import StaffProfile, StaffActivityLog
    out(f"Staff profiles: {StaffProfile.objects.count()}")
    out(f"Approved staff: {StaffProfile.objects.filter(status='approved').count()}")
    out(f"Pending staff: {StaffProfile.objects.filter(status='pending').count()}")
    out(f"Activity records: {StaffActivityLog.objects.count()}")
    out("\nSTAFF PROFILE FIELDS")
    for field in StaffProfile._meta.get_fields():
        out(f"  {field.name}")
    out("\nACTIVITY MODEL FIELDS")
    for field in StaffActivityLog._meta.get_fields():
        out(f"  {field.name}")
except Exception as exc:
    out(f"Staff inspection error: {exc}")

out("\nACTIVE DASHBOARD VIEW")
try:
    match = resolve("/staff/")
    view = inspect.unwrap(match.func)
    out(f"URL name: {match.url_name}")
    out(f"View: {view.__module__}.{view.__name__}")
    out(inspect.getsource(view))
except Exception as exc:
    out(f"View inspection error: {exc!r}")

out("\nDASHBOARD TEMPLATE")
try:
    template = get_template("staff/dashboard.html")
    out(f"Template path: {template.origin.name}")
    out(f"Template size: {len(Path(template.origin.name).read_text(encoding='utf-8'))}")
except Exception as exc:
    out(f"Template inspection error: {exc!r}")

Path("dashboard_repair_report.txt").write_text(
    "\n".join(lines), encoding="utf-8"
)
out("\nReport created: dashboard_repair_report.txt")
