import os
import ast
from pathlib import Path
from django.apps import apps

BASE = Path(__file__).resolve().parent
OUTPUT = Path(os.environ["TLG_AUDIT_REPORT"])
lines = []

def add(text=""):
    lines.append(str(text))

def heading(text):
    add()
    add("=" * 90)
    add(text)
    add("=" * 90)

def read_file(path):
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="cp1252")
        except Exception as exc:
            return f"[Could not decode file: {exc}]"
    except Exception as exc:
        return f"[Could not read file: {exc}]"

def inspect_python_file(relative_path, keywords=None, show_all=False):
    path = BASE / relative_path
    heading(f"SOURCE FILE: {relative_path}")

    if not path.exists():
        add("FILE NOT FOUND")
        return

    source = read_file(path)
    add(f"Path: {path}")
    add(f"Lines: {len(source.splitlines())}")

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        add(f"SYNTAX ERROR: {exc}")
        add(source[:30000])
        return

    source_lines = source.splitlines()
    selected = []

    if show_all:
        add(source)
        return

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name.lower()
            relevant = keywords and any(word.lower() in name for word in keywords)
            if relevant:
                selected.append((node.lineno, getattr(node, "end_lineno", node.lineno), node.name))

    selected.sort()

    if selected:
        for start, end, name in selected:
            add()
            add(f"--- {name} (lines {start}-{end}) ---")
            add("\n".join(source_lines[start - 1:end]))
    else:
        add("No matching function or class names found.")

    if keywords:
        add()
        add("--- Other lines mentioning relevant terms ---")
        terms = [x.lower() for x in keywords]
        matches = []
        for number, line in enumerate(source_lines, 1):
            if any(term in line.lower() for term in terms):
                matches.append(f"{number}: {line}")
        add("\n".join(matches[:500]) if matches else "No matching lines.")

def inspect_urls(relative_path):
    path = BASE / relative_path
    heading(f"URL ROUTES: {relative_path}")
    if path.exists():
        source = read_file(path)
        add(source)
    else:
        add("File not found.")

def inspect_templates():
    heading("SHIPPING AND CHECKOUT TEMPLATE REFERENCES")
    roots = [BASE / "templates", BASE / "products" / "templates",
             BASE / "staff" / "templates"]

    terms = ("shipping", "checkout", "tracking", "carrier",
             "shipment", "order total", "shipping_cost", "ups")

    count = 0
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in (
                ".html", ".txt", ".js", ".css"
            ):
                continue
            content = read_file(path)
            matching = [
                f"{i}: {line.strip()}"
                for i, line in enumerate(content.splitlines(), 1)
                if any(term in line.lower() for term in terms)
            ]
            if matching:
                add()
                add(f"--- {path.relative_to(BASE)} ---")
                add("\n".join(matching[:150]))
                count += 1
    if count == 0:
        add("No matching template files or references found.")

def inspect_models():
    heading("DJANGO MODEL FIELDS")
    for model_name in (
        "ShippingRule", "ShippingSystemSettings", "Order",
        "OrderItem", "Shipment", "Product"
    ):
        try:
            model = apps.get_model("products", model_name)
        except LookupError:
            add(f"\n{model_name}: MODEL NOT FOUND in products app")
            continue

        add(f"\n--- {model._meta.label} ---")
        for field in model._meta.fields:
            details = [
                f"type={field.__class__.__name__}",
                f"null={field.null}",
                f"blank={field.blank}",
            ]
            if field.has_default():
                try:
                    details.append(f"default={field.default}")
                except Exception:
                    pass
            if field.is_relation:
                details.append(f"related_model={field.related_model}")
            add(f"{field.name}: " + ", ".join(details))

        for field in model._meta.many_to_many:
            add(f"{field.name}: many-to-many relation")

        try:
            instance = model.objects.first()
            if instance:
                add("First saved record:")
                for field in model._meta.fields:
                    try:
                        value = getattr(instance, field.name)
                        if field.is_relation and value is not None:
                            value = str(value)
                        add(f"  {field.name} = {value}")
                    except Exception as exc:
                        add(f"  {field.name} = [error: {exc}]")
            else:
                add("No saved records.")
        except Exception as exc:
            add(f"Database read error: {exc}")

def inspect_database():
    heading("DATABASE COUNTS")
    for model_name in (
        "ShippingRule", "ShippingSystemSettings", "Order",
        "OrderItem", "Shipment", "Product"
    ):
        try:
            model = apps.get_model("products", model_name)
            add(f"{model_name}: {model.objects.count()} records")
        except Exception as exc:
            add(f"{model_name}: unavailable ({exc})")

def inspect_project_files():
    heading("PROJECT CONFIGURATION AND SHIPPING-RELATED FILES")
    for relative in (
        "manage.py",
        "products/urls.py",
        "staff/urls.py",
        "swiftcart/urls.py",
        "swiftcart/settings.py",
        "products/admin.py",
        "staff/views.py",
        "staff/models.py",
    ):
        path = BASE / relative
        if not path.exists():
            add(f"{relative}: not found")
            continue

        source = read_file(path)
        add(f"\n--- {relative} ---")
        if relative.endswith("urls.py") or relative.endswith("admin.py"):
            add(source[:30000])
        else:
            matching = [
                f"{i}: {line}"
                for i, line in enumerate(source.splitlines(), 1)
                if any(term in line.lower() for term in (
                    "shipping", "checkout", "shipment", "ups",
                    "order", "installed_apps", "middleware",
                    "staff_shipping"
                ))
            ]
            add("\n".join(matching[:400]) if matching else
                "No matching lines found.")

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")
    import django
    django.setup()

    heading("THE LABEL GROUP - SHIPPING AND CHECKOUT AUDIT")
    add("Purpose: Read-only inspection; no records or source files are modified.")
    add(f"Project: {BASE}")
    add(f"Django version: {django.get_version()}")

    inspect_models()
    inspect_database()

    inspect_python_file(
        "products/views.py",
        keywords=[
            "shipping_quote", "checkout", "order_success",
            "cart", "create_order", "shipment", "ups"
        ]
    )

    inspect_python_file(
        "products/models.py",
        keywords=[
            "ShippingRule", "ShippingSystemSettings",
            "Order", "OrderItem", "Shipment", "Product"
        ]
    )

    inspect_python_file(
        "staff/views.py",
        keywords=["shipping", "order", "shipment", "quote"]
    )

    inspect_urls("products/urls.py")
    inspect_urls("staff/urls.py")
    inspect_project_files()
    inspect_templates()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print("Audit completed.")
    print("Report:", OUTPUT)
    print("Report size:", OUTPUT.stat().st_size, "bytes")
    print("This script did not intentionally modify your website or database.")

if __name__ == "__main__":
    main()
