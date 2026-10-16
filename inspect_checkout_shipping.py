import ast
import os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")
import django
django.setup()

base = Path(__file__).resolve().parent
out = []

for filename, names in [
    ("products/views.py", {"shipping_quote", "checkout"}),
]:
    path = base / filename
    out.append(f"FILE: {filename}")
    source = path.read_text(encoding="utf-8-sig")
    lines = source.splitlines()
    tree = ast.parse(source)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            out.append(f"\n--- {node.name} | lines {node.lineno}-{node.end_lineno} ---")
            out.extend(lines[node.lineno-1:node.end_lineno])

for filename in ["products/urls.py", "staff/urls.py"]:
    path = base / filename
    out.append(f"\n--- RELEVANT ROUTES: {filename} ---")
    if path.exists():
        for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            if any(word in line.lower() for word in ["shipping", "checkout", "order", "shipment"]):
                out.append(f"{number}: {line}")

report = Path(os.environ["TLG_TWO_FUNCTIONS_REPORT"])
report.write_text("\n".join(out), encoding="utf-8")
print("Saved:", report)
print("Lines extracted:", len(out))
print("\n".join(out))
