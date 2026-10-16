from pathlib import Path
from datetime import datetime
from textwrap import dedent, indent
import ast
import shutil
import subprocess
import sys

root = Path.cwd()
vp = root / "staff" / "views.py"
cp = root / "staff" / "templates" / "staff" / "customers.html"
kp = root / "staff" / "templates" / "staff" / "calendar_orders.html"

if not (root / "manage.py").exists() or not vp.exists():
    raise SystemExit("Open PowerShell in your Django project folder.")

# Back up all files that will be changed.
backup = root / "safe_repair_backups" / ("staff_pages_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
backup.mkdir(parents=True, exist_ok=True)
for p in (vp, cp, kp):
    if p.exists():
        shutil.copy2(p, backup / (p.name + ".bak"))

customers_body = dedent("""
    from products.models import Order, QuoteRequest

    search = request.GET.get("search", "").strip()
    people = {}

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
                "last_seen": getattr(record, "created_at", None),
            }
            people[key] = person
        else:
            for field, value in (
                ("name", name), ("email", email),
                ("phone", phone), ("company", company)
            ):
                if value and (not person[field] or person[field] == "Customer"):
                    person[field] = value
            created = getattr(record, "created_at", None)
            if created and (not person["last_seen"] or created > person["last_seen"]):
                person["last_seen"] = created

        person["orders_count" if kind == "order" else "quotes_count"] += 1

    for obj in Order.objects.all().order_by("-created_at"):
        add_person(
            getattr(obj, "customer_name", ""),
            getattr(obj, "customer_email", ""),
            getattr(obj, "customer_phone", ""),
            "", "order", obj
        )

    for obj in QuoteRequest.objects.all().order_by("-created_at"):
        add_person(
            getattr(obj, "customer_name", ""),
            getattr(obj, "customer_email", ""),
            getattr(obj, "customer_phone", ""),
            getattr(obj, "company_name", ""),
            "quote", obj
        )

    customers = list(people.values())
    if search:
        term = search.casefold()
        customers = [
            p for p in customers
            if any(term in str(p.get(f, "") or "").casefold()
                   for f in ("name", "email", "phone", "company"))
        ]

    customers.sort(
        key=lambda p: p["last_seen"] or datetime.min.replace(tzinfo=None),
        reverse=True
    )
    return render(request, "staff/customers.html", {
        "customers": customers,
        "total_customers": len(customers),
        "search": search,
    })
""").strip()

calendar_body = dedent("""
    from django.db.models import Q
    from products.models import Order, CollectionCalendarStickerOrder

    search = request.GET.get("search", "").strip()
    orders = Order.objects.all().order_by("-created_at")
    calendar_orders = CollectionCalendarStickerOrder.objects.all().order_by("-created_at")

    if search:
        orders = orders.filter(
            Q(customer_name__icontains=search) |
            Q(customer_email__icontains=search) |
            Q(status__icontains=search)
        )
        calendar_orders = calendar_orders.filter(
            Q(name__icontains=search) |
            Q(company__icontains=search) |
            Q(email__icontains=search) |
            Q(status__icontains=search)
        )

    return render(request, "staff/calendar_orders.html", {
        "orders": orders,
        "calendar_orders": calendar_orders,
        "search": search,
    })
""").strip()

source = vp.read_text(encoding="utf-8-sig")
tree = ast.parse(source)
nodes = {}

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name in ("staff_customers", "staff_calendar_orders"):
            nodes[node.name] = node

if set(nodes) != {"staff_customers", "staff_calendar_orders"}:
    raise SystemExit("Could not find both view functions. No files were changed.")

# Replace only function bodies; preserve decorators, signatures and access checks.
for name, body in sorted(
    (("staff_customers", customers_body),
     ("staff_calendar_orders", calendar_body)),
    key=lambda item: nodes[item[0]].lineno,
    reverse=True
):
    node = nodes[name]
    lines = source.splitlines(keepends=True)
    start = node.body[0].lineno - 1
    end = node.end_lineno
    replacement = indent(body, "    ") + "\n"
    source = "".join(lines[:start]) + replacement + "".join(lines[end:])

ast.parse(source)
vp.write_text(source, encoding="utf-8")

customers_html = dedent("""
<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Customers | THE LABEL GROUP</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:#202b3c;font:15px/1.5 Arial}
header{background:#0b1f3a;color:white;padding:22px max(18px,calc((100% - 1150px)/2))}
main{max-width:1150px;margin:28px auto;padding:0 18px}
.top{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap}
.panel{background:white;padding:20px;border:1px solid #e0e6ef;border-radius:12px;margin-top:20px}
.muted{color:#667085}a{color:#174f91;text-decoration:none}
input{padding:11px;border:1px solid #ccd4e0;border-radius:7px;min-width:220px}
button{padding:11px 16px;background:#f47b20;color:white;border:0;border-radius:7px;cursor:pointer}
table{width:100%;border-collapse:collapse;min-width:700px}th,td{text-align:left;padding:12px;border-bottom:1px solid #edf0f5}
th{background:#f8fafc;color:#667085;font-size:12px;text-transform:uppercase}
.wrap{overflow-x:auto}.count{background:#eef3fa;border-radius:20px;padding:4px 9px}
</style></head><body>
<header><strong>THE LABEL GROUP</strong><div>Customer relationship directory</div></header>
<main><div class="top"><div><h1>Customers</h1>
<div class="muted">Customer contacts, purchase history and quote activity.</div></div>
<a href="/staff/">&#8592; Staff Dashboard</a></div>
<section class="panel">
<h2>{{ total_customers }} customers</h2>
<form method="get"><input name="search" value="{{ search }}" placeholder="Search name, email, phone or company">
<button>Search</button> <a href="?">Clear</a></form>
<div class="wrap"><table><thead><tr><th>Customer</th><th>Contact</th><th>Company</th><th>Orders</th><th>Quotes</th><th>Last activity</th></tr></thead><tbody>
{% for c in customers %}
<tr><td><strong>{{ c.name }}</strong></td><td>{% if c.email %}<a href="mailto:{{ c.email }}">{{ c.email }}</a>{% else %}No email{% endif %}{% if c.phone %}<div>{{ c.phone }}</div>{% endif %}</td>
<td>{{ c.company|default:"-" }}</td><td><span class="count">{{ c.orders_count }}</span></td>
<td><span class="count">{{ c.quotes_count }}</span></td><td>{% if c.last_seen %}{{ c.last_seen|date:"M j, Y, g:i a" }}{% else %}-{% endif %}</td></tr>
{% empty %}<tr><td colspan="6">No matching customers found.</td></tr>{% endfor %}
</tbody></table></div></section></main></body></html>
""").strip() + "\n"

calendar_html = dedent("""
<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Production &amp; Calendar Orders | THE LABEL GROUP</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:#202b3c;font:15px/1.5 Arial}
header{background:#0b1f3a;color:white;padding:22px max(18px,calc((100% - 1150px)/2))}
main{max-width:1150px;margin:28px auto;padding:0 18px}
.top{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap}
.panel{background:white;padding:20px;border:1px solid #e0e6ef;border-radius:12px;margin-top:20px}
.muted{color:#667085}a{color:#174f91;text-decoration:none}
input{padding:11px;border:1px solid #ccd4e0;border-radius:7px;min-width:220px}
button{padding:11px 16px;background:#f47b20;color:white;border:0;border-radius:7px;cursor:pointer}
table{width:100%;border-collapse:collapse;min-width:680px}th,td{text-align:left;padding:12px;border-bottom:1px solid #edf0f5}
th{background:#f8fafc;color:#667085;font-size:12px;text-transform:uppercase}.wrap{overflow-x:auto}
</style></head><body><header><strong>THE LABEL GROUP</strong><div>Production control centre</div></header>
<main><div class="top"><div><h1>Production &amp; Calendar Orders</h1>
<div class="muted">Review shop orders and dedicated calendar sticker requests.</div></div>
<a href="/staff/">&#8592; Staff Dashboard</a></div>
<section class="panel"><form method="get"><input name="search" value="{{ search }}" placeholder="Search customer, email or status">
<button>Search</button> <a href="?">Clear</a></form>
<h2>Shop Orders</h2><p class="muted">Orders awaiting review or production.</p>
<div class="wrap"><table><thead><tr><th>Order</th><th>Customer</th><th>Email</th><th>Status</th><th>Total</th><th>Date</th></tr></thead><tbody>
{% for o in orders %}<tr><td><a href="/staff/orders/{{ o.pk }}/">#{{ o.pk }}</a></td><td>{{ o.customer_name|default:"-" }}</td>
<td>{{ o.customer_email|default:"-" }}</td><td>{{ o.status|default:"-" }}</td>
<td>{{ o.currency|default:"USD" }} {{ o.total|default:"0.00" }}</td><td>{{ o.created_at|date:"M j, Y, g:i a"|default:"-" }}</td></tr>
{% empty %}<tr><td colspan="6">No shop orders found.</td></tr>{% endfor %}
</tbody></table></div>
<h2>Calendar Sticker Requests</h2><p class="muted">Dedicated calendar orders appear here when submitted.</p>
<div class="wrap"><table><thead><tr><th>Reference</th><th>Customer</th><th>Company</th><th>Email</th><th>Status</th><th>Date</th></tr></thead><tbody>
{% for o in calendar_orders %}<tr><td>#{{ o.pk }}</td><td>{{ o.name|default:"-" }}</td><td>{{ o.company|default:"-" }}</td>
<td>{{ o.email|default:"-" }}</td><td>{{ o.status|default:"-" }}</td><td>{{ o.created_at|date:"M j, Y, g:i a"|default:"-" }}</td></tr>
{% empty %}<tr><td colspan="6">No calendar sticker requests have been submitted.</td></tr>{% endfor %}
</tbody></table></div></section></main></body></html>
""").strip() + "\n"

cp.write_text(customers_html, encoding="utf-8")
kp.write_text(calendar_html, encoding="utf-8")

print("Backups:", backup)
for cmd in (
    [sys.executable, "manage.py", "check"],
    [sys.executable, "manage.py", "shell", "-c",
     "from django.template.loader import get_template; "
     "get_template('staff/customers.html'); "
     "get_template('staff/calendar_orders.html'); "
     "print('Both templates load successfully.')"],
):
    result = subprocess.run(cmd, cwd=root)
    if result.returncode:
        print("Validation failed. Backups are at:", backup)
        raise SystemExit(result.returncode)

print("Repair completed. Existing database records were not changed.")
