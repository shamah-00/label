from pathlib import Path
from datetime import datetime
import ast
import shutil
import subprocess
import sys

ROOT = Path.cwd()
VIEWS = ROOT / "staff" / "views.py"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = ROOT / "backups" / f"label_group_staff_upgrade_{STAMP}"

FILES = [
    VIEWS,
    ROOT / "staff/templates/staff/ops_base.html",
    ROOT / "staff/templates/staff/orders/list.html",
    ROOT / "staff/templates/staff/orders/detail.html",
    ROOT / "staff/templates/staff/customers/list.html",
    ROOT / "staff/templates/staff/calendar_orders/list.html",
    ROOT / "staff/templates/staff/calendar_orders/detail.html",
]

BASE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{% block title %}Staff Control Center{% endblock %} | THE LABEL GROUP</title>
<style>
:root{--navy:#0b1f3a;--dark:#06152a;--orange:#f47b20;--line:#e3e8ef;--muted:#64748b;--paper:#f4f7fb}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:#182334;font:14px/1.5 Arial,Helvetica,sans-serif}
.top{background:linear-gradient(115deg,var(--dark),var(--navy));color:white;padding:22px clamp(16px,4vw,48px);border-bottom:4px solid var(--orange)}
.brand{font-size:22px;font-weight:900;letter-spacing:1.5px}.brand span{color:var(--orange)}
.sub{color:#cbd5e1;font-size:12px;margin-top:3px}
.nav{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}
.nav a{color:white;text-decoration:none;padding:9px 13px;border:1px solid #ffffff2b;border-radius:8px;font-weight:700}
.nav a:hover{background:var(--orange);color:var(--dark)}
main{max-width:1450px;margin:28px auto;padding:0 20px 48px}
h1{font-size:clamp(24px,3vw,34px);margin:0 0 6px;color:var(--navy)}
h2{font-size:18px;color:var(--navy);margin:0 0 14px}
.muted{color:var(--muted)}.intro{margin-bottom:22px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:13px;margin:20px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:0 4px 18px #0b1f3a08}
.metric{font-size:27px;font-weight:900;color:var(--navy);overflow-wrap:anywhere}
.metric-label{color:var(--muted);font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:18px 0}
input,select,textarea{font:inherit;border:1px solid #cbd5e1;border-radius:8px;padding:10px;background:white;color:#172033;max-width:100%}
input,textarea{width:100%}.toolbar input{flex:1;min-width:180px;width:auto}
button,.btn{display:inline-block;background:var(--orange);color:#20170f;border:0;border-radius:8px;padding:10px 15px;font-weight:800;text-decoration:none;cursor:pointer}
.btn.secondary,button.secondary{background:var(--navy);color:white}.btn.light{background:#edf2f7;color:var(--navy)}
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:white}
table{border-collapse:collapse;width:100%;min-width:760px}
th,td{text-align:left;padding:13px 14px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f8fafc;color:#475569;text-transform:uppercase;font-size:11px;letter-spacing:.5px}
tr:last-child td{border-bottom:0}tbody tr:hover{background:#fffaf5}
a{color:#1556a4}td strong{color:var(--navy)}
.pill{display:inline-block;border-radius:30px;background:#e8eef7;color:var(--navy);padding:4px 9px;font-size:11px;font-weight:800;white-space:nowrap}
.pill.pending,.pill.new{background:#fff0d7;color:#8a4b00}
.pill.completed,.pill.delivered,.pill.approved{background:#dcfce7;color:#166534}
.pill.cancelled,.pill.rejected{background:#fee2e2;color:#991b1b}
.pill.processing,.pill.in_production,.pill.shipped{background:#dbeafe;color:#1d4ed8}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,330px),1fr));gap:16px}
.field{margin:14px 0}.field label{display:block;font-weight:800;margin-bottom:6px}
.detail-value{font-size:15px;overflow-wrap:anywhere}.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:15px}
.notice{padding:12px 15px;background:#fff7ed;border-left:4px solid var(--orange);border-radius:7px;margin:12px 0}
.empty{padding:32px;text-align:center;color:var(--muted)}
footer{text-align:center;color:var(--muted);padding:22px;font-size:12px}
@media(max-width:600px){main{padding:0 12px 32px;margin-top:18px}.top{padding:18px 14px}.card,.panel{padding:14px}.metric{font-size:23px}}
</style>
</head>
<body>
<header class="top">
  <div class="brand">THE LABEL <span>GROUP</span></div>
  <div class="sub">INDUSTRIAL PRINTS &amp; DECALS · STAFF OPERATIONS</div>
  <nav class="nav">
    <a href="/staff/">Dashboard</a>
    <a href="/staff/orders/">Orders</a>
    <a href="/staff/customers/">Customers</a>
    <a href="/staff/calendar-orders/">Order Calendar</a>
    <a href="/staff/quotes/">Quote Requests</a>
  </nav>
</header>
<main>
{% if messages %}{% for message in messages %}
<div class="notice">{{ message }}</div>
{% endfor %}{% endif %}
{% block content %}{% endblock %}
</main>
<footer>THE LABEL GROUP · Professional prints that make your brand stick.</footer>
</body>
</html>
'''

ORDERS_LIST = r'''{% extends "staff/ops_base.html" %}
{% block title %}Order Management{% endblock %}
{% block content %}
<div class="intro">
<h1>Order Management</h1>
<div class="muted">Track customer purchases, order value, fulfilment progress and shipping destinations.</div>
</div>
<div class="cards">
<div class="card"><div class="metric">{{ total_orders }}</div><div class="metric-label">All orders</div></div>
<div class="card"><div class="metric">{{ active_orders }}</div><div class="metric-label">Active orders</div></div>
<div class="card"><div class="metric">{{ completed_orders }}</div><div class="metric-label">Completed</div></div>
<div class="card"><div class="metric">{{ total_value|floatformat:2 }}</div><div class="metric-label">Total order value · USD</div></div>
</div>
<section class="panel">
<h2>Find an order</h2>
<form method="get" class="toolbar">
<input type="search" name="search" value="{{ search }}" placeholder="Order number, customer, email, city or status">
<select name="status">
<option value="">All statuses</option>
{% for key,label in status_choices %}
<option value="{{ key }}"{% if status_filter == key %} selected{% endif %}>{{ label }}</option>
{% endfor %}
</select>
<button type="submit">Apply filters</button>
<a class="btn light" href="/staff/orders/">Clear</a>
</form>
</section>
<div class="table-wrap" style="margin-top:18px">
<table>
<thead><tr><th>Order</th><th>Customer</th><th>Destination</th><th>Order value</th><th>Status</th><th>Created</th><th>Updated</th><th></th></tr></thead>
<tbody>
{% for order in orders %}
<tr>
<td><strong>#{{ order.pk }}</strong><br><span class="muted">{{ order.currency|default:"USD" }}</span></td>
<td><strong>{{ order.customer_name }}</strong><br><a href="mailto:{{ order.customer_email }}">{{ order.customer_email }}</a><br>{{ order.customer_phone }}</td>
<td>{{ order.shipping_city }}{% if order.shipping_state %}, {{ order.shipping_state }}{% endif %}<br>{{ order.shipping_country }}</td>
<td><strong>{{ order.currency|default:"USD" }} {{ order.total|floatformat:2 }}</strong><br><span class="muted">Shipping: {{ order.shipping_cost|floatformat:2 }}</span></td>
<td><span class="pill {{ order.status }}">{{ order.get_status_display|default:order.status }}</span></td>
<td>{{ order.created_at|date:"d M Y, H:i" }}</td>
<td>{{ order.updated_at|date:"d M Y, H:i" }}</td>
<td><a class="btn secondary" href="{% url 'staff_order_detail' order.pk %}">Open</a></td>
</tr>
{% empty %}
<tr><td colspan="8" class="empty">No orders match these filters.</td></tr>
{% endfor %}
</tbody>
</table>
</div>
{% endblock %}
'''

ORDER_DETAIL = r'''{% extends "staff/ops_base.html" %}
{% block title %}Order #{{ order.pk }}{% endblock %}
{% block content %}
<div class="intro">
<a href="/staff/orders/">← Back to orders</a>
<h1 style="margin-top:12px">Order #{{ order.pk }}</h1>
<div class="muted">Created {{ order.created_at|date:"d M Y, H:i" }} · Last updated {{ order.updated_at|date:"d M Y, H:i" }}</div>
</div>
<div class="cards">
<div class="card"><div class="metric">{{ order.currency|default:"USD" }} {{ order.total|floatformat:2 }}</div><div class="metric-label">Order total</div></div>
<div class="card"><div class="metric">{{ order.get_status_display|default:order.status }}</div><div class="metric-label">Current status</div></div>
<div class="card"><div class="metric">{{ item_count }}</div><div class="metric-label">Line items</div></div>
</div>
<div class="grid2">
<section class="panel">
<h2>Customer and delivery</h2>
<div class="field"><label>Customer</label><div class="detail-value">{{ order.customer_name }}</div></div>
<div class="field"><label>Email</label><a href="mailto:{{ order.customer_email }}">{{ order.customer_email }}</a></div>
<div class="field"><label>Phone</label>{{ order.customer_phone }}</div>
<div class="field"><label>Shipping address</label>{{ order.shipping_address|linebreaksbr }}</div>
<div class="field"><label>City / State / Postal code</label>{{ order.shipping_city }}{% if order.shipping_state %}, {{ order.shipping_state }}{% endif %} {{ order.shipping_postal_code }}</div>
<div class="field"><label>Country</label>{{ order.shipping_country }}</div>
</section>
<section class="panel">
<h2>Update order</h2>
<form method="post">
{% csrf_token %}
<div class="field"><label for="status">Order status</label>
<select id="status" name="status" required style="width:100%">
{% for key,label in status_choices %}
<option value="{{ key }}"{% if order.status == key %} selected{% endif %}>{{ label }}</option>
{% endfor %}
</select></div>
<div class="field"><label for="notes">Internal order notes</label>
<textarea id="notes" name="notes" rows="7" placeholder="Production, packing, shipping or customer follow-up notes">{{ order.notes }}</textarea></div>
<button type="submit">Save order changes</button>
</form>
<div class="notice">Choose the correct status deliberately. Saving this form will not automatically mark the order completed.</div>
</section>
</div>
<section class="panel" style="margin-top:16px">
<h2>Items ordered</h2>
<div class="table-wrap"><table style="min-width:500px">
<thead><tr><th>Product</th><th>Quantity</th><th>Unit price</th><th>Line total</th></tr></thead>
<tbody>
{% for item in order.items.all %}
<tr><td><strong>{{ item.product_name }}</strong></td><td>{{ item.quantity }}</td><td>{{ order.currency|default:"USD" }} {{ item.unit_price|default_if_none:"0.00"|floatformat:2 }}</td><td>{{ order.currency|default:"USD" }} {{ item.total_price|default_if_none:"0.00"|floatformat:2 }}</td></tr>
{% empty %}<tr><td colspan="4" class="empty">No line items are attached to this order.</td></tr>{% endfor %}
</tbody></table></div>
<div class="actions">
<a class="btn light" href="mailto:{{ order.customer_email }}">Email customer</a>
<a class="btn secondary" href="/staff/orders/">Return to orders</a>
</div>
</section>
{% endblock %}
'''

CUSTOMERS_LIST = r'''{% extends "staff/ops_base.html" %}
{% block title %}Customer Directory{% endblock %}
{% block content %}
<div class="intro">
<h1>Customer Directory</h1>
<div class="muted">A combined view of customers who have placed orders or submitted quote requests.</div>
</div>
<div class="cards">
<div class="card"><div class="metric">{{ total_customers }}</div><div class="metric-label">Customers found</div></div>
<div class="card"><div class="metric">{{ total_order_count }}</div><div class="metric-label">Orders represented</div></div>
<div class="card"><div class="metric">{{ total_quote_count }}</div><div class="metric-label">Quote requests represented</div></div>
<div class="card"><div class="metric">{{ total_customer_spend|floatformat:2 }}</div><div class="metric-label">Recorded order value · USD</div></div>
</div>
<section class="panel">
<form method="get" class="toolbar">
<input type="search" name="search" value="{{ search }}" placeholder="Search name, company, email or phone">
<button type="submit">Search customers</button>
<a class="btn light" href="/staff/customers/">Clear</a>
</form>
</section>
<div class="table-wrap" style="margin-top:18px">
<table>
<thead><tr><th>Customer</th><th>Company</th><th>Contact</th><th>Orders</th><th>Quotes</th><th>Recorded spend</th><th>Latest activity</th></tr></thead>
<tbody>
{% for customer in customers %}
<tr>
<td><strong>{{ customer.name }}</strong></td>
<td>{{ customer.company|default:"—" }}</td>
<td>{% if customer.email %}<a href="mailto:{{ customer.email }}">{{ customer.email }}</a>{% else %}—{% endif %}<br>{{ customer.phone|default:"—" }}</td>
<td><span class="pill">{{ customer.orders_count }}</span></td>
<td><span class="pill">{{ customer.quotes_count }}</span></td>
<td><strong>USD {{ customer.total_spend|floatformat:2 }}</strong></td>
<td>{% if customer.last_seen %}{{ customer.last_seen|date:"d M Y, H:i" }}{% else %}—{% endif %}</td>
</tr>
{% empty %}
<tr><td colspan="7" class="empty">No customers match your search.</td></tr>
{% endfor %}
</tbody>
</table>
</div>
<p class="muted">Recorded spend is calculated from existing order totals. It does not imply that an order has been paid.</p>
{% endblock %}
'''

CALENDAR_LIST = r'''{% extends "staff/ops_base.html" %}
{% block title %}Collection Calendar Orders{% endblock %}
{% block content %}
<div class="intro">
<h1>Collection Calendar Orders</h1>
<div class="muted">Plan production for custom collection calendars and sticker orders using the customer's submitted collection schedule.</div>
</div>
<div class="cards">
<div class="card"><div class="metric">{{ total_calendar_orders }}</div><div class="metric-label">Calendar jobs found</div></div>
<div class="card"><div class="metric">{{ total_quantity }}</div><div class="metric-label">Units requested</div></div>
<div class="card"><div class="metric">{{ active_calendar_orders }}</div><div class="metric-label">Jobs not completed</div></div>
<div class="card"><div class="metric">{{ year_count }}</div><div class="metric-label">Calendar years represented</div></div>
</div>
<section class="panel">
<h2>Find a production job</h2>
<form method="get" class="toolbar">
<input type="search" name="search" value="{{ search }}" placeholder="Job number, company, contact, email, year or status">
<select name="status">
<option value="">All statuses</option>
{% for key,label in status_choices %}
<option value="{{ key }}"{% if status_filter == key %} selected{% endif %}>{{ label }}</option>
{% endfor %}
</select>
<button type="submit">Apply filters</button>
<a class="btn light" href="/staff/calendar-orders/">Clear</a>
</form>
</section>
<div class="table-wrap" style="margin-top:18px">
<table>
<thead><tr><th>Job</th><th>Customer / Company</th><th>Calendar year</th><th>Quantity</th><th>Collection schedule</th><th>Status</th><th>Received</th><th></th></tr></thead>
<tbody>
{% for job in calendar_orders %}
<tr>
<td><strong>#{{ job.pk }}</strong><br>{{ job.title|default:"Collection calendar" }}</td>
<td><strong>{{ job.company|default:job.name }}</strong><br>{{ job.name }}<br>{% if job.email %}<a href="mailto:{{ job.email }}">{{ job.email }}</a>{% endif %}<br>{{ job.phone }}</td>
<td><span class="pill">{{ job.calendar_year }}</span></td>
<td><strong>{{ job.quantity }}</strong></td>
<td><strong>Trash:</strong> {{ job.trash_collection_day|default:"Not specified" }} · {{ job.trash_collection_frequency|default:"Frequency not specified" }}<br><strong>Recycling:</strong> {{ job.recycling_collection_day|default:"Not specified" }} · {{ job.recycling_collection_frequency|default:"Frequency not specified" }}</td>
<td><span class="pill {{ job.status }}">{{ job.get_status_display|default:job.status }}</span></td>
<td>{{ job.created_at|date:"d M Y, H:i" }}</td>
<td><a class="btn secondary" href="{% url 'staff_calendar_order_detail' job.pk %}">Open job</a></td>
</tr>
{% empty %}
<tr><td colspan="8" class="empty">No calendar jobs match these filters.</td></tr>
{% endfor %}
</tbody>
</table>
</div>
<section class="panel" style="margin-top:20px">
<h2>Recent standard orders</h2>
<p class="muted">These are regular ecommerce orders, shown separately from collection calendar production jobs. No delivery deadlines are inferred.</p>
<div class="table-wrap"><table style="min-width:600px">
<thead><tr><th>Order</th><th>Customer</th><th>Status</th><th>Created</th><th></th></tr></thead>
<tbody>
{% for order in recent_orders %}
<tr><td>#{{ order.pk }}</td><td>{{ order.customer_name }}<br>{{ order.customer_email }}</td><td><span class="pill {{ order.status }}">{{ order.get_status_display|default:order.status }}</span></td><td>{{ order.created_at|date:"d M Y, H:i" }}</td><td><a href="{% url 'staff_order_detail' order.pk %}">Open order</a></td></tr>
{% empty %}<tr><td colspan="5" class="empty">No standard orders yet.</td></tr>{% endfor %}
</tbody></table></div>
</section>
{% endblock %}
'''

CALENDAR_DETAIL = r'''{% extends "staff/ops_base.html" %}
{% block title %}Calendar Job #{{ calendar_order.pk }}{% endblock %}
{% block content %}
<div class="intro">
<a href="/staff/calendar-orders/">← Back to order calendar</a>
<h1 style="margin-top:12px">Calendar Job #{{ calendar_order.pk }}</h1>
<div class="muted">Received {{ calendar_order.created_at|date:"d M Y, H:i" }} · Last updated {{ calendar_order.updated_at|date:"d M Y, H:i" }}</div>
</div>
<div class="cards">
<div class="card"><div class="metric">{{ calendar_order.calendar_year }}</div><div class="metric-label">Calendar year</div></div>
<div class="card"><div class="metric">{{ calendar_order.quantity }}</div><div class="metric-label">Units requested</div></div>
<div class="card"><div class="metric">{{ calendar_order.get_status_display|default:calendar_order.status }}</div><div class="metric-label">Job status</div></div>
</div>
<div class="grid2">
<section class="panel">
<h2>Customer and delivery address</h2>
<div class="field"><label>Company</label>{{ calendar_order.company|default:"Not supplied" }}</div>
<div class="field"><label>Contact name</label>{{ calendar_order.name }}</div>
<div class="field"><label>Job title</label>{{ calendar_order.title|default:"Collection calendar" }}</div>
<div class="field"><label>Email</label>{% if calendar_order.email %}<a href="mailto:{{ calendar_order.email }}">{{ calendar_order.email }}</a>{% else %}Not supplied{% endif %}</div>
<div class="field"><label>Phone</label>{{ calendar_order.phone|default:"Not supplied" }}</div>
<div class="field"><label>Address</label>{{ calendar_order.street_address }} {{ calendar_order.address_contd }}<br>{{ calendar_order.city }}{% if calendar_order.state %}, {{ calendar_order.state }}{% endif %} {{ calendar_order.zip_code }}<br>{{ calendar_order.country }}</div>
</section>
<section class="panel">
<h2>Production notes and status</h2>
<form method="post">
{% csrf_token %}
<div class="field"><label for="status">Job status</label><select id="status" name="status" required style="width:100%">
{% for key,label in status_choices %}
<option value="{{ key }}"{% if calendar_order.status == key %} selected{% endif %}>{{ label }}</option>
{% endfor %}
</select></div>
<div class="field"><label for="staff_notes">Internal staff notes</label><textarea id="staff_notes" name="staff_notes" rows="8" placeholder="Artwork, proof approval, print run, finishing, packing and dispatch notes">{{ calendar_order.staff_notes }}</textarea></div>
<button type="submit">Save job updates</button>
</form>
</section>
</div>
<section class="panel" style="margin-top:16px">
<h2>Collection schedule supplied by customer</h2>
<div class="grid2">
<div>
<div class="field"><label>Trash collection</label>{{ calendar_order.trash_collection_day|default:"Not specified" }}</div>
<div class="field"><label>Trash frequency</label>{{ calendar_order.trash_collection_frequency|default:"Not specified" }}</div>
<div class="field"><label>Other trash frequency</label>{{ calendar_order.other_trash_frequency|default:"Not specified" }}</div>
<div class="field"><label>Recycling collection</label>{{ calendar_order.recycling_collection_day|default:"Not specified" }}</div>
<div class="field"><label>Recycling frequency</label>{{ calendar_order.recycling_collection_frequency|default:"Not specified" }}</div>
<div class="field"><label>Other recycling frequency</label>{{ calendar_order.other_recycling_frequency|default:"Not specified" }}</div>
</div>
<div>
<div class="field"><label>Other collection information</label>{{ calendar_order.other_collection_information|default:"No additional information supplied"|linebreaksbr }}</div>
<div class="field"><label>Top bar color</label>{{ calendar_order.top_bar_color|default:"Default" }}</div>
<div class="field"><label>Include company logo</label>{% if calendar_order.include_company_logo %}Yes{% else %}No{% endif %}</div>
<div class="field"><label>New Year's Day</label>{% if calendar_order.new_years_day %}Included{% else %}Not selected{% endif %}</div>
<div class="field"><label>Memorial Day</label>{% if calendar_order.memorial_day %}Included{% else %}Not selected{% endif %}</div>
<div class="field"><label>Independence Day</label>{% if calendar_order.independence_day %}Included{% else %}Not selected{% endif %}</div>
<div class="field"><label>Labor Day</label>{% if calendar_order.labor_day %}Included{% else %}Not selected{% endif %}</div>
<div class="field"><label>Thanksgiving</label>{% if calendar_order.thanksgiving_day %}Included{% else %}Not selected{% endif %}</div>
<div class="field"><label>Christmas</label>{% if calendar_order.christmas_day %}Included{% else %}Not selected{% endif %}</div>
<div class="field"><label>Other holidays</label>{{ calendar_order.other_holiday_1 }} {{ calendar_order.other_holiday_2 }} {{ calendar_order.other_holiday_3 }}</div>
</div>
</div>
<div class="actions"><a class="btn light" href="/staff/calendar-orders/">Return to calendar orders</a></div>
</section>
{% endblock %}
'''

REPLACEMENTS = {
"staff_orders": r'''
@staff_required
def staff_orders(request):
    from django.db.models import Q, Sum
    from decimal import Decimal
    from products.models import Order

    all_orders = Order.objects.all().order_by("-created_at")
    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()
    status_choices = list(Order._meta.get_field("status").choices)

    if search:
        condition = (
            Q(customer_name__icontains=search)
            | Q(customer_email__icontains=search)
            | Q(customer_phone__icontains=search)
            | Q(shipping_city__icontains=search)
            | Q(shipping_country__icontains=search)
            | Q(status__icontains=search)
        )
        if search.isdigit():
            condition |= Q(pk=int(search))
        all_orders = all_orders.filter(condition)

    if status_filter and any(str(k) == status_filter for k, _ in status_choices):
        all_orders = all_orders.filter(status=status_filter)

    all_orders = all_orders.prefetch_related("items")
    status_cards = []
    for key, label in status_choices:
        status_cards.append({
            "key": key,
            "label": label,
            "count": Order.objects.filter(status=key).count(),
        })

    totals = Order.objects.aggregate(value=Sum("total"))
    total_value = totals["value"] or Decimal("0.00")
    active_statuses = [
        key for key, _ in status_choices
        if key not in ("completed", "cancelled")
    ]

    return render(request, "staff/orders/list.html", {
        "orders": all_orders,
        "search": search,
        "status_filter": status_filter,
        "status_choices": status_choices,
        "status_cards": status_cards,
        "total_orders": Order.objects.count(),
        "active_orders": Order.objects.filter(status__in=active_statuses).count(),
        "completed_orders": Order.objects.filter(status="completed").count(),
        "total_value": total_value,
    })
''',
"staff_order_detail": r'''
@staff_required
def staff_order_detail(request, pk):
    from django.contrib import messages
    from products.models import Order

    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        pk=pk,
    )
    status_choices = list(Order._meta.get_field("status").choices)
    allowed_statuses = {str(key) for key, _ in status_choices}

    if request.method == "POST":
        new_status = request.POST.get("status", "").strip()
        new_notes = request.POST.get("notes", order.notes)

        if new_status not in allowed_statuses:
            messages.error(request, "Please choose a valid order status.")
        else:
            changed = []
            if order.status != new_status:
                old_status = order.status
                order.status = new_status
                changed.append(f"status changed from {old_status} to {new_status}")
            if order.notes != new_notes:
                order.notes = new_notes
                changed.append("internal notes updated")

            if changed:
                order.save()
                profile = get_staff_profile(request.user)
                log_staff_activity(
                    request, profile, "update",
                    f"Order #{order.pk}: " + "; ".join(changed),
                    f"Order #{order.pk}",
                )
                messages.success(request, f"Order #{order.pk} has been updated.")
            else:
                messages.info(request, "No changes were needed.")

            return redirect("staff_order_detail", pk=order.pk)

    return render(request, "staff/orders/detail.html", {
        "order": order,
        "status_choices": status_choices,
        "item_count": order.items.count(),
    })
''',
"staff_customers": r'''
@staff_required
def staff_customers(request):
    from collections import defaultdict
    from decimal import Decimal
    from django.db.models import Q
    from products.models import Order, QuoteRequest

    people = {}
    search = request.GET.get("search", "").strip()

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
                "total_spend": Decimal("0.00"),
                "last_seen": getattr(record, "created_at", None),
            }
            people[key] = person
        else:
            for field, value in (
                ("name", name), ("email", email),
                ("phone", phone), ("company", company),
            ):
                if value and (not person[field] or person[field] == "Customer"):
                    person[field] = value
            created = getattr(record, "created_at", None)
            if created and (
                not person["last_seen"]
                or created.timestamp() > person["last_seen"].timestamp()
            ):
                person["last_seen"] = created

        if kind == "order":
            person["orders_count"] += 1
            person["total_spend"] += record.total or Decimal("0.00")
        else:
            person["quotes_count"] += 1

    for obj in Order.objects.all().order_by("-created_at"):
        add_person(
            obj.customer_name, obj.customer_email, obj.customer_phone,
            "", "order", obj,
        )

    for obj in QuoteRequest.objects.all().order_by("-created_at"):
        add_person(
            obj.customer_name, obj.customer_email, obj.customer_phone,
            obj.company_name, "quote", obj,
        )

    customers = list(people.values())
    if search:
        needle = search.casefold()
        customers = [
            p for p in customers
            if any(needle in str(p[field] or "").casefold()
                   for field in ("name", "email", "phone", "company"))
        ]

    customers.sort(
        key=lambda p: p["last_seen"].timestamp() if p["last_seen"] else 0,
        reverse=True,
    )

    total_order_count = sum(p["orders_count"] for p in customers)
    total_quote_count = sum(p["quotes_count"] for p in customers)
    total_customer_spend = sum(
        (p["total_spend"] for p in customers), Decimal("0.00")
    )

    return render(request, "staff/customers/list.html", {
        "customers": customers,
        "total_customers": len(customers),
        "total_order_count": total_order_count,
        "total_quote_count": total_quote_count,
        "total_customer_spend": total_customer_spend,
        "search": search,
    })
''',
"staff_calendar_orders": r'''
@staff_required
def staff_calendar_orders(request):
    from django.db.models import Q, Sum
    from products.models import Order, CollectionCalendarStickerOrder

    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()
    status_choices = list(
        CollectionCalendarStickerOrder._meta.get_field("status").choices
    )

    jobs = CollectionCalendarStickerOrder.objects.all().order_by(
        "-created_at", "-pk"
    )

    if search:
        condition = (
            Q(name__icontains=search)
            | Q(company__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
            | Q(title__icontains=search)
            | Q(status__icontains=search)
        )
        if search.isdigit():
            condition |= Q(pk=int(search)) | Q(calendar_year=int(search))
        jobs = jobs.filter(condition)

    if status_filter and any(str(k) == status_filter for k, _ in status_choices):
        jobs = jobs.filter(status=status_filter)

    summary = jobs.aggregate(quantity=Sum("quantity"))
    total_quantity = summary["quantity"] or 0
    years = jobs.values_list("calendar_year", flat=True).distinct().count()
    completed_keys = {"completed", "cancelled"}
    active_count = jobs.exclude(status__in=completed_keys).count()

    return render(request, "staff/calendar_orders/list.html", {
        "calendar_orders": jobs,
        "recent_orders": Order.objects.all().order_by("-created_at")[:8],
        "search": search,
        "status_filter": status_filter,
        "status_choices": status_choices,
        "total_calendar_orders": jobs.count(),
        "total_quantity": total_quantity,
        "active_calendar_orders": active_count,
        "year_count": years,
    })
''',
"staff_calendar_order_detail": r'''
@staff_required
def staff_calendar_order_detail(request, pk):
    from django.contrib import messages
    from products.models import CollectionCalendarStickerOrder

    calendar_order = get_object_or_404(CollectionCalendarStickerOrder, pk=pk)
    status_field = CollectionCalendarStickerOrder._meta.get_field("status")
    status_choices = [
        (str(key), str(label)) for key, label in status_field.choices if str(key)
    ]
    if not status_choices:
        status_choices = [
            (key, key.replace("_", " ").title())
            for key in ("pending", "reviewing", "approved", "in_production",
                        "completed", "cancelled")
        ]

    allowed_statuses = {key for key, _ in status_choices}

    if request.method == "POST":
        new_status = request.POST.get("status", "").strip()
        new_notes = request.POST.get("staff_notes", calendar_order.staff_notes)

        if new_status not in allowed_statuses:
            messages.error(request, "Please choose a valid job status.")
        else:
            changed = []
            if calendar_order.status != new_status:
                old_status = calendar_order.status
                calendar_order.status = new_status
                changed.append(f"status changed from {old_status} to {new_status}")
            if calendar_order.staff_notes != new_notes:
                calendar_order.staff_notes = new_notes
                changed.append("staff notes updated")

            if changed:
                calendar_order.save()
                profile = get_staff_profile(request.user)
                log_staff_activity(
                    request, profile, "update",
                    f"Calendar job #{calendar_order.pk}: " + "; ".join(changed),
                    f"Calendar job #{calendar_order.pk}",
                )
                messages.success(
                    request, f"Calendar job #{calendar_order.pk} has been updated."
                )
            else:
                messages.info(request, "No changes were needed.")

            return redirect(
                "staff_calendar_order_detail", pk=calendar_order.pk
            )

    return render(request, "staff/calendar_orders/detail.html", {
        "calendar_order": calendar_order,
        "status_choices": status_choices,
    })
'''
}

TEMPLATES = {
    FILES[1]: BASE,
    FILES[2]: ORDERS_LIST,
    FILES[3]: ORDER_DETAIL,
    FILES[4]: CUSTOMERS_LIST,
    FILES[5]: CALENDAR_LIST,
    FILES[6]: CALENDAR_DETAIL,
}

def main():
    original_bytes = {}
    for path in FILES:
        original_bytes[path] = path.read_bytes() if path.exists() else None

    # Parse and verify all target views before touching any project file.
    source = VIEWS.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    targets = set(REPLACEMENTS)
    found = {name: [] for name in targets}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.col_offset == 0:
            if node.name in targets:
                found[node.name].append(node)

    missing = [name for name, nodes in found.items() if not nodes]
    if missing:
        raise RuntimeError(
            "No changes made. Could not find these view definitions: "
            + ", ".join(missing)
        )

    # Make a timestamped copy of every existing file that will be changed.
    for path in FILES:
        if path.exists():
            destination = BACKUP / path.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)

    try:
        lines = source.splitlines(keepends=True)
        edits = []

        for name, nodes in found.items():
            replacement = REPLACEMENTS[name].strip("\n") + "\n\n"
            for node in nodes:
                first_line = min(
                    [d.lineno for d in node.decorator_list] or [node.lineno]
                ) - 1
                last_line = node.end_lineno
                edits.append((first_line, last_line, replacement))

        # Replace from bottom to top so original line indexes stay valid.
        for start, end, replacement in sorted(edits, reverse=True):
            lines[start:end] = [replacement]

        updated_views = "".join(lines)
        compile(updated_views, str(VIEWS), "exec")
        VIEWS.write_text(updated_views, encoding="utf-8")

        for path, content in TEMPLATES.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, "manage.py", "check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        print("\n===== DJANGO SYSTEM CHECK =====")
        print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip())

        if result.returncode != 0:
            raise RuntimeError("Django system check failed; rolling back changed files.")

        print("\nSUCCESS: staff pages upgraded.")
        print("Backup folder:", BACKUP)
        print("Updated views:", VIEWS)
        print("Updated/created templates:")
        for path in TEMPLATES:
            print(" -", path.relative_to(ROOT))
        print("\nNext: run python manage.py runserver and test the staff pages.")

    except Exception:
        print("\nUpgrade failed. Restoring the original files...")
        for path, content in original_bytes.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        print("Rollback complete. Your original files have been restored.")
        print("Backup folder:", BACKUP)
        raise

if __name__ == "__main__":
    main()
