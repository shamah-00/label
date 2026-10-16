from pathlib import Path

view_path = Path("products/views.py")
template_path = Path("templates/products/product_list.html")

view = view_path.read_text(encoding="utf-8-sig")
template = template_path.read_text(encoding="utf-8-sig")

# Fix the catalogue heading.
old_heading = "Shop the THE LABEL GROUP catalogue."
new_heading = "Shop The Label Group Catalogue"

if new_heading not in template:
    if template.count(old_heading) != 1:
        raise SystemExit(
            "Could not uniquely locate the catalogue heading. "
            "No files were changed."
        )
    template = template.replace(old_heading, new_heading, 1)
    print("Updated catalogue heading.")
else:
    print("Catalogue heading is already corrected.")

# Sort Construction products by product code ascending, without
# changing the order of other industry catalogues.
marker = '''    return render(
        request,
        "products/home_new.html" if False else "products/product_list.html",'''

insertion = '''    if industry_filter == "construction":
        products = products.order_by("product_code", "id")

    return render(
        request,
        "products/home_new.html" if False else "products/product_list.html",'''

if 'products = products.order_by("product_code", "id")' not in view:
    if view.count(marker) != 1:
        raise SystemExit(
            "Could not uniquely locate the product-list render block. "
            "No files were changed."
        )
    view = view.replace(marker, insertion, 1)
    print("Added ascending Construction product ordering.")
else:
    print("Construction ascending ordering is already present.")

view_path.write_text(view, encoding="utf-8")
template_path.write_text(template, encoding="utf-8")
print("File updates complete.")
