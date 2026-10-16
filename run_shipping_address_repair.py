from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

root = Path.cwd()
path = root / "staff" / "views.py"

if not path.is_file():
    raise SystemExit("staff/views.py not found.")

original = path.read_text(encoding="utf-8")
views = original

# Confirm the previous safety and delivery-date changes still exist.
for marker in (
    "THE_LABEL_GROUP_ALLOW_LIVE_SHIPPO_PURCHASES",
    "shipment.estimated_delivery = delivery_date",
    'if action == "update":',
):
    if marker not in views:
        raise SystemExit(
            f"Required existing code was not found: {marker}. No files changed."
        )

# Find the shipment queryset, then the address-display loop and its final assignment.
query_marker = 'shipments = list(Shipment.objects.select_related("order").order_by("-updated_at"))'
query_pos = views.find(query_marker)

if query_pos < 0:
    raise SystemExit("Shipment queryset not found. No files changed.")

loop_start = views.find("    for shipment in shipments:", query_pos)
assignment = views.find(
    '        shipment.shipping_destination = ", ".join(parts)',
    loop_start
)

if loop_start < 0 or assignment < 0:
    raise SystemExit(
        "Could not locate the current address-display loop. No files changed."
    )

# Ensure the block ends before the view's final render statement.
render_pos = views.find('    return render(request, "staff/shipping/dashboard.html"', assignment)

if render_pos < 0 or assignment > render_pos:
    raise SystemExit(
        "Could not verify the end of the address-display block. No files changed."
    )

# Include the assignment's newline in the replacement range.
block_end = assignment + len(
    '        shipment.shipping_destination = ", ".join(parts)'
)
if block_end < len(views) and views[block_end:block_end + 2] == "\r\n":
    block_end += 2
elif block_end < len(views) and views[block_end] == "\n":
    block_end += 1

replacement = '''    # Build a display-only address without repeating city, state or ZIP.
    # Original order address fields are not modified.
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
                str(field or "").replace("\\r", " ").replace("\\n", " ").split()
            ).strip(" ,")

            if not text_value:
                continue

            for raw_part in text_value.split(","):
                part = " ".join(raw_part.split()).strip(" ,")
                key = " ".join(part.casefold().split())

                if not key or key in seen:
                    continue

                # Avoid appending city/state/ZIP when already included in
                # a previously displayed address component.
                already_included = any(
                    key in " ".join(existing.casefold().split())
                    or " ".join(existing.casefold().split()) in key
                    for existing in parts
                )

                if already_included:
                    continue

                seen.add(key)
                parts.append(part)

        shipment.shipping_destination = ", ".join(parts)
'''

updated = views[:loop_start] + replacement + views[block_end:]

# Final preflight before creating the backup or writing.
if updated == original:
    raise SystemExit("No changes were needed.")

if "THE_LABEL_GROUP_ALLOW_LIVE_SHIPPO_PURCHASES" not in updated:
    raise SystemExit("Shippo safety check failed. No files changed.")

if "shipment.estimated_delivery = delivery_date" not in updated:
    raise SystemExit("Delivery-date handling check failed. No files changed.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = root / f"shipping_address_repair_backup_{stamp}"
backup.mkdir()
shutil.copy2(path, backup / "views.py")

try:
    path.write_text(updated, encoding="utf-8", newline="\n")

    # Syntax validation first.
    compile(updated, str(path), "exec")

    result = subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=root,
        text=True,
    )

    if result.returncode:
        shutil.copy2(backup / "views.py", path)
        print("Django check failed. Original views.py restored from backup.")
        raise SystemExit(result.returncode)

except Exception:
    if path.exists() and (backup / "views.py").exists():
        # Restore only if the file was actually changed and validation failed.
        if path.read_text(encoding="utf-8") != original:
            shutil.copy2(backup / "views.py", path)
    raise

print("SUCCESS: Shipping address display logic updated.")
print("SUCCESS: Estimated delivery-date handling preserved.")
print("SUCCESS: Shippo live-purchase safety guard preserved.")
print("SUCCESS: Django system check passed.")
print(f"Backup: {backup}")
print("No order records were changed.")
print("No Shippo API requests or label purchases were made.")
