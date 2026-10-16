from pathlib import Path
import re

root = Path.cwd()
views_path = root / "products" / "views.py"
urls_path = root / "products" / "urls.py"
template_path = root / "products" / "templates" / "track_order.html"

views = views_path.read_text(encoding="utf-8-sig")
urls = urls_path.read_text(encoding="utf-8-sig")

marker = "# THE_LABEL_GROUP_CUSTOMER_TRACKING_VIEW"

view_code = r'''

# THE_LABEL_GROUP_CUSTOMER_TRACKING_VIEW
def track_order(request):
    from urllib.parse import quote
    from django.shortcuts import render
    from .models import Order, Shipment

    order = None
    shipment = None
    tracking_url = ""
    error_message = ""
    email_value = ""
    order_number = ""

    if request.method == "POST":
        order_number = request.POST.get("order_number", "").strip().lstrip("#").strip()
        email_value = request.POST.get("email", "").strip()

        if not order_number or not email_value:
            error_message = "Enter both your order number and checkout email."
        elif not order_number.isdigit():
            error_message = "Please enter a valid numeric order number."
        else:
            order = Order.objects.filter(
                pk=int(order_number),
                customer_email__iexact=email_value
            ).first()

            if order is None:
                error_message = (
                    "We couldn't find an order matching those details. "
                    "Check your order number and the email used at checkout."
                )
            else:
                try:
                    shipment = order.shipment
                except Shipment.DoesNotExist:
                    shipment = None

                if shipment and shipment.tracking_number:
                    tracking_number = quote(shipment.tracking_number.strip(), safe="")
                    carrier = (shipment.carrier or "").lower()

                    if "ups" in carrier:
                        tracking_url = (
                            "https://www.ups.com/track?tracknum=" + tracking_number
                        )
                    elif "fedex" in carrier:
                        tracking_url = (
                            "https://www.fedex.com/fedextrack/?trknbr=" + tracking_number
                        )
                    elif "usps" in carrier:
                        tracking_url = (
                            "https://tools.usps.com/go/TrackConfirmAction?tLabels="
                            + tracking_number
                        )
                    elif "dhl" in carrier:
                        tracking_url = (
                            "https://www.dhl.com/global-en/home/tracking.html?tracking-id="
                            + tracking_number
                        )

    status_steps = [
        {"value": "pending", "label": "Order received"},
        {"value": "confirmed", "label": "Order confirmed"},
        {"value": "processing", "label": "Being prepared"},
        {"value": "packed", "label": "Packed"},
        {"value": "shipped", "label": "Shipped"},
        {"value": "completed", "label": "Completed"},
    ]

    current_step = -1
    is_cancelled = False
    if order:
        status_value = (order.status or "").lower()
        is_cancelled = status_value == "cancelled"
        for index, step in enumerate(status_steps):
            if step["value"] == status_value:
                current_step = index

        # If a shipment has progressed further than the order status,
        # show the recorded shipment progress without claiming live carrier data.
        if shipment:
            shipment_status = (shipment.status or "").lower()
            shipment_rank = {
                "pending": 0,
                "processing": 2,
                "packed": 3,
                "shipped": 4,
                "in_transit": 4,
                "out_for_delivery": 4,
                "delivered": 5,
            }
            current_step = max(
                current_step,
                shipment_rank.get(shipment_status, -1)
            )

    context = {
        "order": order,
        "shipment": shipment,
        "tracking_url": tracking_url,
        "error_message": error_message,
        "email_value": email_value,
        "order_number": order_number,
        "status_steps": status_steps,
        "current_step": current_step,
        "is_cancelled": is_cancelled,
    }
    return render(request, "track_order.html", context)
'''

if marker not in views:
    views = views.rstrip() + "\n\n" + view_code.lstrip() + "\n"
    views_path.write_text(views, encoding="utf-8")
    print("Added customer tracking view.")
else:
    print("Customer tracking view already exists; left unchanged.")

route = '    path("track-order/", views.track_order, name="track_order"),'
if 'name="track_order"' not in urls:
    anchor = '    path("order-success/<int:order_id>/", views.order_success, name="order_success"),'
    if anchor not in urls:
        raise SystemExit(
            "Could not find the expected order-success URL. "
            "No tracking URL was added; restore from backup if needed."
        )
    urls = urls.replace(anchor, anchor + "\n" + route, 1)
    urls_path.write_text(urls, encoding="utf-8")
    print("Added /track-order/ URL.")
else:
    print("Tracking URL already exists; left unchanged.")

template_path.parent.mkdir(parents=True, exist_ok=True)
template = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Track Your Order | The Label Group</title>
<style>
:root{--navy:#0b1f3a;--navy-dark:#06152a;--orange:#f47b20;--orange-dark:#d9620d;--ink:#172337;--muted:#64748b;--line:#e2e8f0;--surface:#f5f7fb}
*{box-sizing:border-box}
body{margin:0;background:var(--surface);color:var(--ink);font-family:Arial,Helvetica,sans-serif;line-height:1.55}
header{background:var(--navy);color:white;padding:20px 6%;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
.brand{font-size:21px;font-weight:800;letter-spacing:.5px}
.brand span{color:var(--orange)}
header a{color:white;text-decoration:none;font-weight:700}
main{width:min(920px,92%);margin:38px auto 60px}
.intro{text-align:center;margin-bottom:25px}
.intro h1{color:var(--navy);font-size:clamp(28px,5vw,39px);margin:0 0 8px}
.intro p{color:var(--muted);margin:0}
.card{background:white;border:1px solid var(--line);border-radius:16px;padding:clamp(20px,4vw,32px);box-shadow:0 8px 26px #0b1f3a0b;margin-bottom:22px}
h2{color:var(--navy);font-size:21px;margin:0 0 18px}
form{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.field{display:flex;flex-direction:column;gap:7px}
label{font-weight:700;font-size:14px}
input{width:100%;padding:13px 14px;border:1px solid #cbd5e1;border-radius:9px;font:inherit}
input:focus{outline:2px solid #f47b2055;border-color:var(--orange)}
button,.button{display:inline-block;background:var(--orange);color:#111827;border:0;border-radius:9px;padding:13px 18px;font-size:15px;font-weight:800;text-decoration:none;cursor:pointer;text-align:center}
button:hover,.button:hover{background:var(--orange-dark);color:white}
.submit{grid-column:1/-1}
.error{background:#fff1f0;border:1px solid #fecaca;color:#991b1b;padding:13px 15px;border-radius:9px;margin-bottom:18px}
.success{background:#f0fdf4;border:1px solid #bbf7d0;padding:15px;border-radius:10px;margin-bottom:20px}
.order-head{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;align-items:flex-start}
.order-id{font-size:24px;font-weight:800;color:var(--navy)}
.muted{color:var(--muted);font-size:14px}
.pill{display:inline-block;background:#fff1e6;color:#8a3b00;border-radius:999px;padding:7px 12px;font-size:13px;font-weight:800;text-transform:capitalize}
.timeline{list-style:none;padding:0;margin:24px 0 6px}
.timeline li{display:flex;align-items:flex-start;gap:13px;position:relative;padding-bottom:22px}
.timeline li:last-child{padding-bottom:0}
.dot{width:24px;height:24px;flex:0 0 24px;border:2px solid #cbd5e1;background:white;border-radius:50%;position:relative;z-index:1}
.timeline li.done .dot{background:var(--orange);border-color:var(--orange)}
.timeline li:not(:last-child):after{content:"";position:absolute;left:11px;top:24px;bottom:0;width:2px;background:#e2e8f0}
.timeline li.done:not(:last-child):after{background:#f7bd8d}
.timeline strong{display:block;color:var(--navy)}
.timeline li:not(.done) strong{color:#94a3b8}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.detail{background:#f8fafc;border-radius:10px;padding:14px;min-width:0}
.detail .label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.5px}
.detail .value{font-weight:700;overflow-wrap:anywhere;margin-top:4px}
.items{width:100%;border-collapse:collapse;margin-top:10px}
.items th,.items td{padding:12px 8px;border-bottom:1px solid var(--line);text-align:left}
.items th{font-size:12px;text-transform:uppercase;color:var(--muted)}
.items td:last-child,.items th:last-child{text-align:right}
.total-row{display:flex;justify-content:space-between;gap:12px;padding:8px 0}
.grand{font-size:19px;font-weight:800;color:var(--navy);border-top:1px solid var(--line);margin-top:8px;padding-top:15px}
.notice{background:#f8fafc;border-radius:10px;padding:13px;color:#475569;font-size:14px;margin-top:16px}
.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:20px}
.secondary{background:#eaf0f7;color:var(--navy)}
footer{text-align:center;color:var(--muted);padding:20px;font-size:13px}
@media(max-width:600px){form,.grid{grid-template-columns:1fr}.submit{grid-column:auto}.items th,.items td{padding:10px 4px;font-size:13px}}
</style>
</head>
<body>
<header>
  <div class="brand">THE <span>LABEL</span> GROUP</div>
  <a href="/">Back to shop</a>
</header>
<main>
  <section class="intro">
    <h1>Track your order</h1>
    <p>Check the latest order and shipping updates saved by our team.</p>
  </section>

  <section class="card">
    <h2>Find your order</h2>
    {% if error_message %}<div class="error" role="alert">{{ error_message }}</div>{% endif %}
    <form method="post" action="{% url 'track_order' %}">
      {% csrf_token %}
      <div class="field">
        <label for="order_number">Order number</label>
        <input id="order_number" name="order_number" value="{{ order_number }}" placeholder="For example, 1042" required inputmode="numeric" autocomplete="off">
      </div>
      <div class="field">
        <label for="email">Email used at checkout</label>
        <input id="email" name="email" type="email" value="{{ email_value }}" placeholder="you@example.com" required autocomplete="email">
      </div>
      <div class="submit"><button type="submit">Find my order</button></div>
    </form>
    <p class="muted">Your order number is the number shown on your order confirmation page.</p>
  </section>

  {% if order %}
  <section class="card">
    <div class="order-head">
      <div>
        <div class="muted">ORDER DETAILS</div>
        <div class="order-id">Order #{{ order.id }}</div>
        <div class="muted">Placed {{ order.created_at|date:"M j, Y" }}</div>
      </div>
      <span class="pill">{{ order.get_status_display }}</span>
    </div>

    {% if is_cancelled %}
      <div class="error" style="margin-top:20px;margin-bottom:0">This order has been cancelled. Please contact us if you need assistance.</div>
    {% else %}
      <h2 style="margin-top:28px">Order progress</h2>
      <ol class="timeline">
      {% for step in status_steps %}
        <li class="{% if forloop.counter0 <= current_step %}done{% endif %}">
          <span class="dot"></span>
          <div><strong>{{ step.label }}</strong>
          {% if forloop.counter0 == current_step %}<span class="muted">Current recorded stage</span>{% endif %}</div>
        </li>
      {% endfor %}
      </ol>
    {% endif %}
    <p class="muted">This timeline reflects updates recorded in our system. It does not independently confirm live carrier scans.</p>
  </section>

  <section class="card">
    <h2>Items in your order</h2>
    <div style="overflow-x:auto">
      <table class="items">
        <thead><tr><th>Product</th><th>Qty</th><th>Total</th></tr></thead>
        <tbody>
        {% for item in order.items.all %}
          <tr>
            <td>{{ item.product_name }}</td>
            <td>{{ item.quantity }}</td>
            <td>${{ item.total_price|floatformat:2 }}</td>
          </tr>
        {% empty %}
          <tr><td colspan="3">No order items were found.</td></tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    <div style="max-width:360px;margin:18px 0 0 auto">
      <div class="total-row"><span>Subtotal</span><strong>${{ order.subtotal|floatformat:2 }}</strong></div>
      <div class="total-row"><span>Shipping</span><strong>${{ order.shipping_cost|floatformat:2 }}</strong></div>
      <div class="total-row grand"><span>Total</span><strong>${{ order.total|floatformat:2 }}</strong></div>
    </div>
  </section>

  <section class="card">
    <h2>Shipping information</h2>
    {% if shipment %}
      <div class="grid">
        <div class="detail"><div class="label">Shipping status</div><div class="value">{{ shipment.get_status_display }}</div></div>
        <div class="detail"><div class="label">Carrier</div><div class="value">{{ shipment.carrier|default:"Not assigned yet" }}</div></div>
        <div class="detail"><div class="label">Tracking number</div><div class="value">{{ shipment.tracking_number|default:"Not available yet" }}</div></div>
        <div class="detail"><div class="label">Estimated delivery</div><div class="value">{% if shipment.estimated_delivery %}{{ shipment.estimated_delivery|date:"M j, Y" }}{% else %}Not available yet{% endif %}</div></div>
      </div>
      {% if shipment.status == "delivered" %}
        <div class="success" style="margin-top:16px;margin-bottom:0">Our system records this shipment as delivered.</div>
      {% endif %}
      {% if tracking_url %}
        <div class="actions"><a class="button" href="{{ tracking_url }}" target="_blank" rel="noopener noreferrer">Track with carrier ↗</a></div>
      {% elif shipment.tracking_number %}
        <p class="notice">A tracking number is saved, but an automatic carrier link is not available for this carrier. Use the carrier's official website to track the parcel.</p>
      {% endif %}
    {% else %}
      <p class="muted">A shipment record has not been added to this order yet. Please check again later.</p>
    {% endif %}
    <div class="notice">Shipping and delivery updates on this page come from the information recorded by The Label Group. Live carrier tracking is available through the carrier link when supported.</div>
  </section>
  {% endif %}
</main>
<footer>© The Label Group · Industrial Prints &amp; Decals</footer>
</body>
</html>
'''
template_path.write_text(template, encoding="utf-8")
print(f"Created customer tracking template: {template_path}")
