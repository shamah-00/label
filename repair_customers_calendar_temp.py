from pathlib import Path
from datetime import datetime
import ast
import shutil
import subprocess
import sys

ROOT = Path.cwd()
VIEWS = ROOT / "staff" / "views.py"
TEMPLATE_DIR = ROOT / "staff" / "templates" / "staff"
CUSTOMERS_TEMPLATE = TEMPLATE_DIR / "customers.html"
CALENDAR_TEMPLATE = TEMPLATE_DIR / "calendar_orders.html"

if not (ROOT / "manage.py").exists() or not VIEWS.exists():
    raise SystemExit(
        "STOP: Run this from your ecommerce project folder "
        "containing manage.py and staff/views.py."
    )

# Verify existing Python code before making changes.
preflight = subprocess.run(
    [sys.executable, "manage.py", "check"],
    cwd=ROOT, capture_output=True, text=True
)
print("PRE-REPAIR DJANGO CHECK:")
print(preflight.stdout)
if preflight.returncode != 0:
    print(preflight.stderr)
    raise SystemExit("Stopped without changing files because the initial check failed.")

original_source = VIEWS.read_text(encoding="utf-8", errors="replace")
tree = ast.parse(original_source)

wanted = {"staff_customers", "staff_calendar_orders"}
functions = {
    node.name: node
    for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name in wanted
}

missing = wanted - set(functions)
if missing:
    raise SystemExit(
        "STOP: Could not safely find these top-level view functions: "
        + ", ".join(sorted(missing))
        + ". No files were changed."
    )

# Create a timestamped backup before editing anything.
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = ROOT / "safe_repair_backups" / ("customers_calendar_" + stamp)
backup_dir.mkdir(parents=True, exist_ok=True)

targets = [VIEWS, CUSTOMERS_TEMPLATE, CALENDAR_TEMPLATE]
existed = {p: p.exists() for p in targets}

for path in targets:
    if path.exists():
        backup_path = backup_dir / path.relative_to(ROOT)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)

print("Backup folder:", backup_dir)

customer_body = '''
    from django.shortcuts import render
    from products.models import Order, QuoteRequest

    search = (request.GET.get("search") or "").strip()
    customers_by_key = {}

    def customer_key(name, email, phone, source, record_id):
        normalized_email = (email or "").strip().lower()
        if normalized_email:
            return "email:" + normalized_email

        normalized_name = (name or "").strip().lower()
        normalized_phone = (phone or "").strip().lower()

        if normalized_name or normalized_phone:
            return "contact:{}|{}".format(normalized_name, normalized_phone)

        return "{}:{}".format(source, record_id)

    def add_customer(name, email, phone, company, source, record):
        key = customer_key(name, email, phone, source, record.pk)
        customer = customers_by_key.get(key)

        if customer is None:
            customer = {
                "name": name or "Customer",
                "email": email or "",
                "phone": phone or "",
                "company": company or "",
                "orders_count": 0,
                "quotes_count": 0,
                "last_seen": getattr(record, "created_at", None),
            }
            customers_by_key[key] = customer
        else:
            if not customer["name"] or customer["name"] == "Customer":
                customer["name"] = name or customer["name"]
            if not customer["email"]:
                customer["email"] = email or ""
            if not customer["phone"]:
                customer["phone"] = phone or ""
            if not customer["company"]:
                customer["company"] = company or ""

            created = getattr(record, "created_at", None)
            if created and (
                not customer["last_seen"] or created > customer["last_seen"]
            ):
                customer["last_seen"] = created

        if source == "order":
            customer["orders_count"] += 1
        else:
            customer["quotes_count"] += 1

    for order in Order.objects.all().order_by("-created_at"):
        add_customer(
            getattr(order, "customer_name", ""),
            getattr(order, "customer_email", ""),
            getattr(order, "customer_phone", ""),
            "",
            "order",
            order,
        )

    for quote in QuoteRequest.objects.all().order_by("-created_at"):
        add_customer(
            getattr(quote, "customer_name", ""),
            getattr(quote, "customer_email", ""),
            getattr(quote, "customer_phone", ""),
            getattr(quote, "company_name", ""),
            "quote",
            quote,
        )

    customers = list(customers_by_key.values())

    if search:
        term = search.casefold()
        customers = [
            customer for customer in customers
            if any(
                term in str(value or "").casefold()
                for value in (
                    customer["name"],
                    customer["email"],
                    customer["phone"],
                    customer["company"],
                )
            )
        ]

    customers.sort(
        key=lambda item: (item["last_seen"] is not None, item["last_seen"]),
        reverse=True,
    )

    return render(request, "staff/customers.html", {
        "customers": customers,
        "search": search,
        "query": search,
        "total_customers": len(customers),
    })
'''

calendar_body = '''
    from django.shortcuts import render
    from products.models import Order, CollectionCalendarStickerOrder

    search = (request.GET.get("search") or "").strip()

    # General customer orders already in the database.
    orders = list(Order.objects.all().order_by("-created_at"))

    # Dedicated collection-calendar sticker orders.
    calendar_orders = list(
        CollectionCalendarStickerOrder.objects.all().order_by("-created_at")
    )

    if search:
        term = search.casefold()

        def matches(record, fields):
            return any(
                term in str(getattr(record, field, "") or "").casefold()
                for field in fields
            ) or term in str(record.pk)

        orders = [
            obj for obj in orders
            if matches(
                obj,
                ("customer_name", "customer_email", "customer_phone", "status"),
            )
        ]

        calendar_orders = [
            obj for obj in calendar_orders
            if matches(
                obj,
                ("name", "company", "email", "phone", "status", "calendar_year"),
            )
        ]

    return render(request, "staff/calendar_orders.html", {
        "orders": orders,
        "order_list": orders,
        "calendar_orders": calendar_orders,
        "search": search,
        "total_orders": len(orders),
        "total_calendar_orders": len(calendar_orders),
    })
'''

customers_html = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Staff Customers | THE LABEL GROUP</title>
<style>
:root{--navy:#0b1f3a;--orange:#f47b20;--bg:#f3f6fa;--muted:#667085}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);font:15px/1.5 Arial,sans-serif;color:#202b3c}
header{background:var(--navy);color:white;padding:24px max(20px,calc((100% - 1180px)/2))}
header strong{font-size:21px;letter-spacing:.5px}
header p{margin:5px 0 0;color:#d7e1ef}
main{max-width:1180px;margin:28px auto;padding:0 18px}
.top{display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap}
h1{margin:0 0 6px;font-size:27px}
.muted{color:var(--muted)}
a{color:#174f91;text-decoration:none}
a:hover{text-decoration:underline}
.back{display:inline-block;background:white;border:1px solid #d7deea;border-radius:8px;padding:10px 14px}
.panel{background:white;border:1px solid #e0e6ef;border-radius:13px;padding:20px;margin-top:20px;box-shadow:0 4px 16px #172b4d0a}
.stats{font-size:14px;color:var(--muted);margin:0 0 15px}
form{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
input{flex:1;min-width:190px;border:1px solid #cbd5e1;border-radius:8px;padding:12px;font:inherit}
button{background:var(--orange);color:white;border:0;border-radius:8px;padding:12px 18px;font-weight:bold;cursor:pointer}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;min-width:690px}
th,td{text-align:left;padding:13px 11px;border-bottom:1px solid #edf0f5;vertical-align:top}
th{font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);background:#f8fafc}
td strong{color:var(--navy)}
.count{display:inline-block;background:#eef3fa;border-radius:20px;padding:4px 9px;margin:2px;font-size:12px}
.empty{text-align:center;padding:35px 12px;color:var(--muted)}
@media(max-width:600px){main{margin:18px auto;padding:0 12px}h1{font-size:23px}.panel{padding:13px}}
</style>
</head>
<body>
<header>
<strong>THE LABEL GROUP</strong>
<p>Staff workspace · Customer directory</p>
</header>
<main>
<div class="top">
<div><h1>Staff Customers</h1><div class="muted">Customers from your existing orders and quote requests.</div></div>
<a class="back" href="/staff/">← Back to Dashboard</a>
</div>
<section class="panel">
<p class="stats">Customers matching this view: <strong>{{ total_customers }}</strong></p>
<form method="get" action="">
<input type="search" name="search" value="{{ search }}" placeholder="Search name, email, phone or company">
<button type="submit">Search</button>
<a class="back" href="/staff/customers/">Clear</a>
</form>
<div class="table-wrap">
<table>
<thead><tr><th>Customer</th><th>Contact</th><th>Company</th><th>Orders</th><th>Quotes</th><th>Last activity</th></tr></thead>
<tbody>
{% for customer in customers %}
<tr>
<td><strong>{{ customer.name }}</strong></td>
<td>{% if customer.email %}<a href="mailto:{{ customer.email }}">{{ customer.email }}</a>{% else %}<span class="muted">No email</span>{% endif %}
{% if customer.phone %}<div>{{ customer.phone }}</div>{% endif %}</td>
<td>{{ customer.company|default:"—" }}</td>
<td><span class="count">{{ customer.orders_count }}</span></td>
<td><span class="count">{{ customer.quotes_count }}</span></td>
<td>{% if customer.last_seen %}{{ customer.last_seen|date:"M j, Y, g:i a" }}{% else %}—{% endif %}</td>
</tr>
{% empty %}
<tr><td colspan="6" class="empty">{% if search %}No customers match “{{ search }}”. Try another search.{% else %}No customers have been recorded yet.{% endif %}</td></tr>
{% endfor %}
</tbody>
</table>
</div>
</section>
</main>
</body>
</html>
'''

calendar_html = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Production &amp; Calendar Orders | THE LABEL GROUP</title>
<style>
:root{--navy:#0b1f3a;--orange:#f47b20;--bg:#f3f6fa;--muted:#667085}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);font:15px/1.5 Arial,sans-serif;color:#202b3c}
header{background:var(--navy);color:white;padding:24px max(20px,calc((100% - 1180px)/2))}
header strong{font-size:21px;letter-spacing:.5px}
header p{margin:5px 0 0;color:#d7e1ef}
main{max-width:1180px;margin:28px auto;padding:0 18px}
.top{display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap}
h1{margin:0 0 6px;font-size:27px}
h2{font-size:20px;color:var(--navy);margin:0 0 14px}
.muted{color:var(--muted)}
.back{display:inline-block;background:white;border:1px solid #d7deea;border-radius:8px;padding:10px 14px;color:#174f91;text-decoration:none}
.panel{background:white;border:1px solid #e0e6ef;border-radius:13px;padding:20px;margin-top:20px;box-shadow:0 4px 16px #172b4d0a}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}
.stat{background:white;border:1px solid #e0e6ef;border-radius:10px;padding:15px 18px;min-width:155px}
.stat strong{display:block;font-size:25px;color:var(--navy)}
.stat span{color:var(--muted);font-size:13px}
form{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 18px}
input{flex:1;min-width:190px;border:1px solid #cbd5e1;border-radius:8px;padding:12px;font:inherit}
button{background:var(--orange);color:white;border:0;border-radius:8px;padding:12px 18px;font-weight:bold;cursor:pointer}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;min-width:650px}
th,td{text-align:left;padding:13px 11px;border-bottom:1px solid #edf0f5;vertical-align:top}
th{font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);background:#f8fafc}
td strong{color:var(--navy)}
.badge{display:inline-block;background:#edf3fb;border-radius:20px;padding:4px 9px;font-size:12px}
.empty{text-align:center;padding:28px 12px;color:var(--muted)}
@media(max-width:600px){main{margin:18px auto;padding:0 12px}h1{font-size:23px}.panel{padding:13px}}
</style>
</head>
<body>
<header><strong>THE LABEL GROUP</strong><p>Staff workspace · Production and order tracking</p></header>
<main>
<div class="top">
<div><h1>Production &amp; Calendar Orders</h1><div class="muted">Track existing customer orders and collection-calendar orders.</div></div>
<a class="back" href="/staff/">← Back to Dashboard</a>
</div>
<div class="stats">
<div class="stat"><strong>{{ total_orders }}</strong><span>Customer orders</span></div>
<div class="stat"><strong>{{ total_calendar_orders }}</strong><span>Calendar sticker orders</span></div>
</div>
<section class="panel">
<h2>Customer Orders</h2>
<form method="get" action="">
<input type="search" name="search" value="{{ search }}" placeholder="Search customer, email, phone or status">
<button type="submit">Search</button>
<a class="back" href="/staff/calendar-orders/">Clear</a>
</form>
<div class="table-wrap"><table>
<thead><tr><th>Order #</th><th>Customer</th><th>Order date</th><th>Total</th><th>Status</th><th>Details</th></tr></thead>
<tbody>
{% for order in orders %}
<tr>
<td><strong>#{{ order.pk }}</strong></td>
<td>{{ order.customer_name|default:"Customer" }}<div class="muted">{{ order.customer_email|default:"" }}</div></td>
<td>{% if order.created_at %}{{ order.created_at|date:"M j, Y, g:i a" }}{% else %}—{% endif %}</td>
<td>{{ order.currency|default:"USD" }} {{ order.total|default:"0.00" }}</td>
<td><span class="badge">{{ order.get_status_display|default:order.status|default:"Pending" }}</span></td>
<td><a href="/staff/orders/{{ order.pk }}/">View order →</a></td>
</tr>
{% empty %}
<tr><td colspan="6" class="empty">{% if search %}No customer orders match “{{ search }}”.{% else %}No customer orders have been recorded yet.{% endif %}</td></tr>
{% endfor %}
</tbody></table></div>
</section>
<section class="panel">
<h2>Collection Calendar Sticker Orders</h2>
<div class="table-wrap"><table>
<thead><tr><th>Record #</th><th>Customer / Company</th><th>Calendar year</th><th>Created</th><th>Status</th><th>Details</th></tr></thead>
<tbody>
{% for item in calendar_orders %}
<tr>
<td><strong>#{{ item.pk }}</strong></td>
<td>{{ item.name|default:"Customer" }}<div class="muted">{{ item.company|default:"" }}</div><div>{{ item.email|default:"" }}</div></td>
<td>{{ item.calendar_year|default:"—" }}</td>
<td>{% if item.created_at %}{{ item.created_at|date:"M j, Y" }}{% else %}—{% endif %}</td>
<td><span class="badge">{{ item.get_status_display|default:item.status|default:"Pending" }}</span></td>
<td><a href="/staff/calendar-orders/{{ item.pk }}/">View record →</a></td>
</tr>
{% empty %}
<tr><td colspan="6" class="empty">No collection-calendar sticker orders have been recorded yet. Existing customer orders are listed above.</td></tr>
{% endfor %}
</tbody></table></div>
</section>
</main>
</body>
</html>
'''

def replace_function_body(lines, node, body):
    # Keep the original function signature and decorators.
    start = node.body[0].lineno - 1
    end = node.end_lineno
    replacement = body.strip("\n").splitlines()
    lines[start:end] = replacement

changed = []

try:
    lines = original_source.splitlines()
    # Replace from bottom to top so earlier line numbers remain valid.
    replacements = [
        (functions["staff_customers"], customer_body),
        (functions["staff_calendar_orders"], calendar_body),
    ]
    for node, body in sorted(replacements, key=lambda pair: pair[0].lineno, reverse=True):
        replace_function_body(lines, node, body)

    new_source = "\n".join(lines) + "\n"
    ast.parse(new_source)
    VIEWS.write_text(new_source, encoding="utf-8")
    changed.append(VIEWS)

    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    CUSTOMERS_TEMPLATE.write_text(customers_html, encoding="utf-8")
    changed.append(CUSTOMERS_TEMPLATE)

    CALENDAR_TEMPLATE.write_text(calendar_html, encoding="utf-8")
    changed.append(CALENDAR_TEMPLATE)

    # Validate Django and compile the templates; do not alter ALLOWED_HOSTS.
    check = subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=ROOT, capture_output=True, text=True
    )
    print("\n========== DJANGO CHECK ==========")
    print(check.stdout)
    if check.returncode != 0:
        print(check.stderr)
        raise RuntimeError("Django system check failed.")

    template_test = r'''
from django.template.loader import get_template
from django.urls import reverse
from products.models import Order, QuoteRequest, CollectionCalendarStickerOrder

for name in ("staff/customers.html", "staff/calendar_orders.html"):
    get_template(name)
    print("TEMPLATE OK:", name)

for name in ("staff_customers", "staff_calendar_orders", "staff_dashboard"):
    try:
        print("URL OK:", name, "=>", reverse(name))
    except Exception as exc:
        print("URL NAME NOT FOUND:", name, "-", exc)

print("ORDERS PRESERVED:", Order.objects.count())
print("QUOTES PRESERVED:", QuoteRequest.objects.count())
print("CALENDAR ORDERS:", CollectionCalendarStickerOrder.objects.count())
'''
    test = subprocess.run(
        [sys.executable, "manage.py", "shell", "-c", template_test],
        cwd=ROOT, capture_output=True, text=True
    )
    print("\n========== TEMPLATE AND DATA VALIDATION ==========")
    print(test.stdout)
    if test.returncode != 0:
        print(test.stderr)
        raise RuntimeError("Template or data validation failed.")

    print("\nSUCCESS: Customer and Production & Calendar Orders pages repaired.")
    print("Backup:", backup_dir)
    print("Open these pages after restarting/reloading the development server:")
    print("  http://127.0.0.1:8000/staff/customers/")
    print("  http://127.0.0.1:8000/staff/calendar-orders/")

except Exception as exc:
    print("\nREPAIR VALIDATION FAILED:", exc)
    print("Attempting to restore the original files from the backup.")

    for path in targets:
        backup_path = backup_dir / path.relative_to(ROOT)
        if existed[path] and backup_path.exists():
            shutil.copy2(backup_path, path)
        elif not existed[path] and path.exists():
            path.unlink()

    print("Restoration attempt complete. Backup folder:", backup_dir)
    raise SystemExit(1)
