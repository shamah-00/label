from pathlib import Path
from datetime import datetime
import re
import shutil
import subprocess
import sys

root = Path.cwd()
views_path = root / "staff" / "views.py"
shipping_template = root / "staff" / "templates" / "staff" / "shipping" / "dashboard.html"
order_template = root / "staff" / "templates" / "staff" / "orders" / "detail.html"

for path in (views_path, shipping_template, order_template):
    if not path.is_file():
        raise SystemExit(f"Required file not found: {path}")

views = views_path.read_text(encoding="utf-8")
shipping_html = shipping_template.read_text(encoding="utf-8")
order_html = order_template.read_text(encoding="utf-8")

# Refuse to patch a different or unexpected implementation.
required = [
    'if action == "purchase_label":',
    'if action == "update":',
    'shipment.status = status',
    'shipment.save()',
    'shipment.shipping_destination = ", ".join(parts)',
]
for marker in required:
    if marker not in views:
        raise SystemExit(
            "Repair stopped without changing files: expected code was not found: "
            + marker
        )

# Protect against accidental real Shippo purchases by default.
purchase_marker = 'if action == "purchase_label":'
guard = '''if action == "purchase_label":
            live_purchase_enabled = os.environ.get(
                "THE_LABEL_GROUP_ALLOW_LIVE_SHIPPO_PURCHASES", ""
            ).strip().lower() in {"1", "true", "yes"}

            if not live_purchase_enabled:
                messages.error(
                    request,
                    "Shippo label purchasing is disabled for safety. "
                    "Verify the order, destination, parcel, rate and cost, "
                    "and explicitly enable live purchasing only when authorized."
                )
                return redirect("staff_shipping_dashboard")
'''
if 'THE_LABEL_GROUP_ALLOW_LIVE_SHIPPO_PURCHASES' not in views:
    views = views.replace(purchase_marker, guard, 1)

# Add delivery-date parsing and validation before mutating the shipment.
status_marker = '''            shipment.status = status
            shipment.tracking_number = request.POST.get(
'''
status_replacement = '''            from django.utils.dateparse import parse_date

            delivery_raw = request.POST.get("estimated_delivery", "").strip()
            delivery_date = parse_date(delivery_raw) if delivery_raw else None
            if delivery_raw and delivery_date is None:
                messages.error(request, "Enter a valid estimated delivery date.")
                return redirect("staff_shipping_dashboard")

            shipment.status = status
            shipment.estimated_delivery = delivery_date
            shipment.tracking_number = request.POST.get(
'''
if 'shipment.estimated_delivery = delivery_date' not in views:
    if status_marker not in views:
        raise SystemExit("Repair stopped: shipment update block did not match.")
    views = views.replace(status_marker, status_replacement, 1)

# Stamp delivered/shipped dates only once, and synchronize compatible order statuses.
sync_marker = '''            shipment.save()
            messages.success(request, "Shipment details updated.")
            return redirect("staff_shipping_dashboard")
'''
sync_replacement = '''            shipment.save()

            # Keep the order status aligned with shipment progress when supported.
            order = shipment.order
            shipment_to_order = {
                "processing": "processing",
                "packed": "packed",
                "shipped": "shipped",
                "in_transit": "shipped",
                "out_for_delivery": "shipped",
                "delivered": "completed",
                "cancelled": "cancelled",
            }
            desired_order_status = shipment_to_order.get(status)
            if desired_order_status and (order.status or "").lower() != "cancelled":
                try:
                    field = order._meta.get_field("status")
                    choices = {value for value, label in field.choices}
                    if desired_order_status in choices:
                        order.status = desired_order_status
                        order.save(update_fields=["status"])
                except Exception:
                    # Shipment changes remain saved if the order model differs.
                    pass

            messages.success(request, "Shipment details updated.")
            return redirect("staff_shipping_dashboard")
'''
if 'shipment_to_order = {' not in views:
    if sync_marker not in views:
        raise SystemExit("Repair stopped: shipment save block did not match.")
    views = views.replace(sync_marker, sync_replacement, 1)

# Improve destination display: remove exact duplicates and components already
# contained in another comma-separated address component.
address_start = '    # Create a clean display address without repeating address components.\n'
address_end = '        shipment.shipping_destination = ", ".join(parts)\n'
start = views.find(address_start)
end = views.find(address_end, start)
if start < 0 or end < 0:
    raise SystemExit("Repair stopped: address-formatting block did not match.")

end += len(address_end)
new_address = '''    # Display each address component once, including overlapping city/state/ZIP data.
    for shipment in shipments:
        order = shipment.order
        address_fields = [
            getattr(order, "shipping_address", ""),
            getattr(order, "shipping_city", ""),
            getattr(order, "shipping_state", ""),
            getattr(order, "shipping_postal_code", ""),
            getattr(order, "shipping_country", ""),
        ]

        parts = []
        seen = set()

        for field in address_fields:
            text_value = " ".join(
                str(field or "").replace("\\\\r", " ").replace("\\\\n", " ").split()
            ).strip(" ,")
            if not text_value:
                continue

            for raw_part in text_value.split(","):
                part = " ".join(raw_part.split()).strip(" ,")
                key = part.casefold()
                if not key or key in seen:
                    continue

                words = set(re.findall(r"[a-z0-9]+", key))
                already_represented = False
                for existing in parts:
                    existing_words = set(
                        re.findall(r"[a-z0-9]+", existing.casefold())
                    )
                    if words and existing_words and (
                        words.issubset(existing_words)
                        or existing_words.issubset(words)
                    ):
                        already_represented = True
                        break

                if not already_represented:
                    parts.append(part)
                    seen.add(key)

        shipment.shipping_destination = ", ".join(parts)
'''
views = views[:start] + new_address + views[end:]

# Add a date input to the existing shipment update form if it has the expected field.
tracking_input = '''                        <div class="shipping-field">
                            <label for="tracking-{{ shipment.id }}">Tracking number</label>
                            <input id="tracking-{{ shipment.id }}" name="tracking_number"
                                   value="{{ shipment.tracking_number }}" maxlength="200">
                        </div>
'''
date_input = '''                        <div class="shipping-field">
                            <label for="delivery-{{ shipment.id }}">Estimated delivery</label>
                            <input id="delivery-{{ shipment.id }}" name="estimated_delivery"
                                   type="date"
                                   value="{{ shipment.estimated_delivery|date:'Y-m-d' }}">
                        </div>

''' + tracking_input

if 'name="estimated_delivery"' not in shipping_html:
    if tracking_input not in shipping_html:
        raise SystemExit(
            "Repair stopped: could not find the shipment tracking input to add delivery date."
        )
    shipping_html = shipping_html.replace(tracking_input, date_input, 1)

# Fix obvious template references to .qty instead of the model's .quantity field.
order_html, qty_fixes = re.subn(
    r'\b((?:item|order_item|line_item))\.qty\b',
    r'\1.quantity',
    order_html,
)

# Replace a misleading quantity fallback if it is attached to a quantity expression.
order_html, quantity_fallback_fixes = re.subn(
    r'(\b(?:item|order_item|line_item)\.quantity)\|default:"Not provided"',
    r'\1',
    order_html,
)

# Validate all changes before writing anything.
if 'THE_LABEL_GROUP_ALLOW_LIVE_SHIPPO_PURCHASES' not in views:
    raise SystemExit("Repair stopped: Shippo safety guard was not installed.")
if 'shipment.estimated_delivery = delivery_date' not in views:
    raise SystemExit("Repair stopped: estimated delivery save was not installed.")
if 'shipment_to_order = {' not in views:
    raise SystemExit("Repair stopped: status synchronization was not installed.")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = root / f"shipping_repair_backup_{timestamp}"
backup.mkdir()

targets = {
    views_path: views,
    shipping_template: shipping_html,
    order_template: order_html,
}

for original in targets:
    shutil.copy2(original, backup / original.name)

# Save repaired files only after preflight checks and backups succeed.
for path, content in targets.items():
    path.write_text(content, encoding="utf-8", newline="\n")

print(f"Backup created: {backup}")
print("Updated staff/views.py")
print("Updated staff/templates/staff/shipping/dashboard.html")
print("Updated staff/templates/staff/orders/detail.html")
print(f"Quantity template fixes: {qty_fixes + quantity_fallback_fixes}")
print("No database records were edited.")
print("No Shippo request or label purchase was made.")

# Django validation.
result = subprocess.run(
    [sys.executable, "manage.py", "check"],
    cwd=root,
    text=True,
)
if result.returncode:
    print("Django check failed. Restore the backed-up files before continuing.")
    raise SystemExit(result.returncode)
print("Django system check passed.")
