from pathlib import Path
import ast
import shutil
import sys

path = Path("products/views.py")
source = path.read_text(encoding="utf-8-sig")
tree = ast.parse(source)

checkout = next(
    (node for node in ast.walk(tree)
     if isinstance(node, ast.FunctionDef) and node.name == "checkout"),
    None,
)

if checkout is None:
    sys.exit("ERROR: checkout() was not found. No changes made.")

lines = source.splitlines(keepends=True)
start, end = checkout.lineno - 1, checkout.end_lineno
function_source = "".join(lines[start:end])

old = '''    if not cache_valid:
        request.session.pop(SESSION_RATES, None)
        request.session.pop(SESSION_SIGNATURE, None)
        request.session.pop(SESSION_TIME, None)
        return render_checkout(
            items,
            subtotal,
            error=(
                "Your shipping rates have expired or your address/cart changed. "
                "Calculate shipping again and select a service."
            ),
        )
'''

new = '''    # Recalculate server-side if the cached rate expired or changed.
    if not cache_valid:
        try:
            cached_rates = get_configured_shipping_rates(
                address, packages, subtotal
            )
        except ValueError as exc:
            request.session.pop(SESSION_RATES, None)
            request.session.pop(SESSION_SIGNATURE, None)
            request.session.pop(SESSION_TIME, None)
            return render_checkout(items, subtotal, error=str(exc))

        if not cached_rates:
            return render_checkout(
                items, subtotal,
                error="No shipping estimate is available. Please try again.",
            )

        request.session[SESSION_RATES] = cached_rates
        request.session[SESSION_SIGNATURE] = signature
        request.session[SESSION_TIME] = time.time()
        request.session.modified = True

'''

if old not in function_source:
    sys.exit(
        "STOP: The expected code block was not found. "
        "No changes were made. Please share this message with ChatGPT."
    )

old_selection = '''    selected_id = request.POST.get("shipping_rate_id", "").strip()
    selected_rate = next(
'''

new_selection = '''    selected_id = request.POST.get("shipping_rate_id", "").strip()
    if not selected_id and len(cached_rates) == 1:
        selected_id = cached_rates[0].get("object_id", "")

    selected_rate = next(
'''

if old_selection not in function_source:
    sys.exit(
        "STOP: The expected rate-selection code was not found. "
        "No changes were made."
    )

backup = Path("products/views.py.backup_checkout_rate_recovery")
if not backup.exists():
    shutil.copy2(path, backup)

function_source = function_source.replace(old, new, 1)
function_source = function_source.replace(old_selection, new_selection, 1)

updated = "".join(lines[:start]) + function_source + "".join(lines[end:])

# Validate the whole file before writing anything.
ast.parse(updated)
path.write_text(updated, encoding="utf-8")

print("SUCCESS: Checkout rate recovery updated.")
print("Backup:", backup)
print("Python syntax validated.")
