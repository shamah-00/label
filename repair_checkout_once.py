from pathlib import Path
from datetime import datetime
import shutil
import re

root = Path.cwd()
views_file = root / "products" / "views.py"
urls_file = root / "products" / "urls.py"
template_file = root / "products" / "templates" / "order_success.html"

if not views_file.exists() or not urls_file.exists():
    raise SystemExit("ERROR: products/views.py or products/urls.py was not found. No changes made.")

views = views_file.read_text(encoding="utf-8-sig")
urls = urls_file.read_text(encoding="utf-8-sig")

if re.search(r"^\s*def\s+checkout\s*\(", views, re.M):
    raise SystemExit("A checkout view already exists. Stopped without changing files to avoid overwriting it.")

if not re.search(r"^\s*def\s+cart\s*\(", views, re.M):
    raise SystemExit("Could not find the cart view. No changes made.")

if "name='checkout'" in urls or 'name="checkout"' in urls:
    raise SystemExit("A checkout URL already exists. Stopped to avoid adding a duplicate route.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = root / f"checkout_repair_backup_{stamp}"
backup.mkdir()
for file in (views_file, urls_file):
    shutil.copy2(file, backup / file.name)
if template_file.exists():
    shutil.copy2(template_file, backup / template_file.name)

checkout_code = r'''

# ============================================================
# CUSTOMER CHECKOUT AND ORDER CONFIRMATION
# ============================================================

def checkout(request):
    from decimal import Decimal
    from django.contrib import messages
    from django.db import transaction
    from django.shortcuts import render, redirect
    from .models import Product, Order, OrderItem

    def get_checkout_items():
        result = []
        session_cart = request.session.get("cart", {})
        for product_id, quantity in session_cart.items():
            try:
                product = Product.objects.get(pk=int(product_id), is_available=True)
                quantity = max(1, int(quantity))
                line_total = product.price * quantity
                result.append({
                    "product": product,
                    "quantity": quantity,
                    "subtotal": line_total,
                    "total_price": line_total,
                })
            except (Product.DoesNotExist, ValueError, TypeError):
                continue
        return result

    checkout_items = get_checkout_items()
    subtotal = sum((item["subtotal"] for item in checkout_items), Decimal("0.00"))
    shipping_cost = Decimal("0.00")
    total = subtotal + shipping_cost

    context = {
        "checkout_items": checkout_items,
        "cart_items": checkout_items,
        "items": checkout_items,
        "subtotal": subtotal,
        "cart_total": subtotal,
        "shipping_cost": shipping_cost,
        "total": total,
        "grand_total": total,
    }

    if not checkout_items:
        messages.error(request, "Your cart is empty or its products are unavailable.")
        return redirect("cart")

    if request.method == "POST":
        customer_name = request.POST.get("customer_name", "").strip()
        customer_email = request.POST.get("customer_email", "").strip()
        customer_phone = request.POST.get("customer_phone", "").strip()
        shipping_address = request.POST.get("shipping_address", "").strip()
        shipping_city = request.POST.get("shipping_city", "").strip()
        shipping_state = request.POST.get("shipping_state", "").strip()
        shipping_postal_code = request.POST.get("shipping_postal_code", "").strip()
        shipping_country = request.POST.get("shipping_country", "").strip()
        notes = request.POST.get("notes", "").strip()

        required = {
            "name": customer_name,
            "email": customer_email,
            "phone": customer_phone,
            "shipping address": shipping_address,
            "city": shipping_city,
            "country": shipping_country,
        }
        missing = [label for label, value in required.items() if not value]
        if missing:
            messages.error(request, "Please complete these required fields: " + ", ".join(missing) + ".")
            return render(request, "checkout.html", context)

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    customer_name=customer_name,
                    customer_email=customer_email,
                    customer_phone=customer_phone,
                    shipping_address=shipping_address,
                    shipping_city=shipping_city,
                    shipping_state=shipping_state,
                    shipping_postal_code=shipping_postal_code,
                    shipping_country=shipping_country,
                    subtotal=subtotal,
                    shipping_cost=shipping_cost,
                    total=total,
                    currency="USD",
                    status="pending",
                    notes=notes,
                )

                for item in checkout_items:
                    product = item["product"]
                    quantity = item["quantity"]
                    unit_price = product.price
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=unit_price * quantity,
                        currency="USD",
                    )

        except Exception:
            messages.error(request, "We could not save your order. Your cart has been kept. Please try again.")
            return render(request, "checkout.html", context)

        request.session["cart"] = {}
        request.session["last_order_id"] = order.pk
        request.session.modified = True
        messages.success(request, f"Your order #{order.pk} has been placed successfully.")
        return redirect("order_success", order_id=order.pk)

    return render(request, "checkout.html", context)


def order_success(request, order_id):
    from django.shortcuts import render, get_object_or_404
    from .models import Order

    order = get_object_or_404(Order, pk=order_id)
    return render(request, "order_success.html", {"order": order})
'''

views = views.rstrip() + "\n" + checkout_code + "\n"

checkout_routes = '''    path("checkout/", views.checkout, name="checkout"),
    path("order-success/<int:order_id>/", views.order_success, name="order_success"),
'''

cart_route = re.search(
    r"(?m)^\s*path\(['\"]cart/['\"],\s*views\.cart,\s*name=['\"]cart['\"]\),\s*$",
    urls
)
if cart_route:
    urls = urls[:cart_route.start()] + checkout_routes + urls[cart_route.start():]
else:
    closing = urls.rfind("]")
    if closing < 0:
        raise SystemExit("Could not safely locate the end of products/urls.py. No application files changed.")
    urls = urls[:closing] + checkout_routes + urls[closing:]

success_html = """{% extends "base.html" %}
{% block content %}
<section style="max-width:760px;margin:60px auto;padding:32px 24px;text-align:center;font-family:Arial,sans-serif;">
  <h1 style="color:#0b1f3a;">Thank you for your order!</h1>
  <p>Your order has been saved successfully.</p>
  <h2>Order #{{ order.id }}</h2>
  <p><strong>Status:</strong> {{ order.get_status_display|default:order.status }}</p>
  <p><strong>Total:</strong> ${{ order.total|floatformat:2 }} {{ order.currency }}</p>
  <h3>Order items</h3>
  <ul style="display:inline-block;text-align:left;">
    {% for item in order.items.all %}
      <li>{{ item.product_name }} × {{ item.quantity }} — ${{ item.total_price|floatformat:2 }}</li>
    {% endfor %}
  </ul>
  <p>Our team can now view this order in the staff orders dashboard.</p>
  <a href="{% url 'product_list' %}" style="display:inline-block;margin-top:20px;padding:12px 20px;background:#f47b20;color:white;text-decoration:none;border-radius:6px;">Continue Shopping</a>
</section>
{% endblock %}
"""

views_file.write_text(views, encoding="utf-8")
urls_file.write_text(urls, encoding="utf-8")
if not template_file.exists():
    template_file.write_text(success_html, encoding="utf-8")

print("Checkout view and URLs added.")
print("Order confirmation template created if it did not already exist.")
print("Backup saved to:", backup)