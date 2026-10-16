from pathlib import Path
from datetime import datetime
import re
import shutil

from products.models import Product

views_path = Path("products/views.py")
template_path = Path("templates/products/product_detail.html")

views = views_path.read_text(encoding="utf-8")
template = template_path.read_text(encoding="utf-8")

# Only target the intended Construction category, not old duplicate-code
# records in other categories.
products = list(
    Product.objects.filter(
        category="construction",
        product_code__regex=r"^C[0-9]{3}$"
    ).order_by("product_code", "id")
)

if not products:
    raise RuntimeError("No Construction-category C-code products found.")

codes = [p.product_code for p in products]
print("Construction-category records:", len(products))
print("Codes:", ", ".join(codes))

# Parse both formats:
# Standard size: 5" x 7"
# Standard Size
# 5" x 7"
# Also supports Ideal Material, Finish, Primary Application,
# and What to Include / Buyer's Notes.
new_function = r'''def product_detail(request, product_id):
    import re

    product = get_object_or_404(Product, id=product_id)
    context = {"product": product}

    code = str(getattr(product, "product_code", "") or "").upper()
    category = str(getattr(product, "category", "") or "").strip().lower()

    if category == "construction" and re.fullmatch(r"C\d{3}", code):
        description = str(getattr(product, "description", "") or "")
        lines = description.replace("\r\n", "\n").replace("\r", "\n").split("\n")

        label_map = {
            "standard size": "standard_size",
            "primary application": "application",
            "buyer's notes": "buyer_notes",
            "what to include / buyer's notes": "buyer_notes",
            "what to include / buyer’s notes": "buyer_notes",
            "ideal material": "ideal_material",
            "finish": "finish",
            "adhesive": "adhesive",
            "printing method": "printing_method",
        }

        def normalize_label(value):
            return re.sub(r"\s+", " ", value.strip().rstrip(":")).lower()

        parsed = {}
        description_lines = []
        current_field = None

        for line in lines:
            stripped = line.strip()

            # Handle labels written on their own line, with or without a colon.
            heading_match = re.match(r"^([^:]+?)\s*:\s*(.*)$", stripped)
            if heading_match:
                possible_label = normalize_label(heading_match.group(1))
                if possible_label in label_map:
                    current_field = label_map[possible_label]
                    value = heading_match.group(2).strip()
                    if value:
                        parsed.setdefault(current_field, []).append(value)
                    continue

            possible_label = normalize_label(stripped)
            if possible_label in label_map:
                current_field = label_map[possible_label]
                continue

            # Ignore old placeholder headings that were saved as description text.
            if possible_label in ("description", "product description"):
                current_field = None
                continue

            if current_field:
                if stripped:
                    parsed.setdefault(current_field, []).append(stripped)
            else:
                description_lines.append(line)

        def field_value(key):
            return " ".join(parsed.get(key, [])).strip()

        base_description = "\n".join(description_lines).strip()
        base_description = re.sub(
            r"(?i)^\s*description\s*:?\s*",
            "",
            base_description
        ).strip()

        context["construction_specs"] = {
            "description": base_description,
            "standard_size": field_value("standard_size"),
            "application": field_value("application"),
            "buyer_notes": field_value("buyer_notes"),
            "ideal_material": field_value("ideal_material"),
            "finish": field_value("finish"),
            "adhesive": field_value("adhesive"),
            "printing_method": field_value("printing_method"),
        }

    return render(request, "products/product_detail.html", context)
'''

view_pattern = re.compile(
    r"(?ms)^def product_detail\(request,\s*product_id\):.*?(?=^(?:def |class |@)|\Z)"
)
view_match = view_pattern.search(views)

if not view_match:
    raise RuntimeError("Could not safely locate product_detail. No files were written.")

updated_views = (
    views[:view_match.start()]
    + new_function
    + "\n\n"
    + views[view_match.end():].lstrip("\n")
)

# Use the extracted standard size in the existing size row.
size_pattern = re.compile(
    r'(<th scope="row">\s*\{% if product\.industry == "construction" '
    r'and product\.product_code\|slice:":1" == "C" %\}Standard Size'
    r'\{% else %\}Shape\{% endif %\}\s*</th>\s*<td>)'
    r'\{\{\s*product\.shape\s*\}\}'
    r'(</td>)',
    re.S
)

updated_template, size_replacements = size_pattern.subn(
    r'\1{% if construction_specs and construction_specs.standard_size %}'
    r'{{ construction_specs.standard_size }}'
    r'{% else %}{{ product.shape }}{% endif %}\2',
    template,
    count=1
)

if size_replacements != 1:
    raise RuntimeError(
        "Could not match the existing size row exactly. No files were written."
    )

# Verify the existing description/application/notes rows are present.
required_template_parts = [
    "construction_specs.description",
    "construction_specs.application",
    "construction_specs.buyer_notes",
]
for part in required_template_parts:
    if part not in updated_template:
        raise RuntimeError(
            f"Expected template section {part!r} was not found. No files were written."
        )

# Back up both files before writing.
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
views_backup = views_path.with_name(f"views.before_construction_fix_{stamp}.py")
template_backup = template_path.with_name(
    f"product_detail.before_construction_fix_{stamp}.html"
)

shutil.copy2(views_path, views_backup)
shutil.copy2(template_path, template_backup)

views_path.write_text(updated_views, encoding="utf-8")
template_path.write_text(updated_template, encoding="utf-8")

print("\nUpdated Construction detail parser and size display.")
print("Backups:")
print(" ", views_backup)
print(" ", template_backup)

# Verify all intended records without modifying their product data.
print("\n=== CONSTRUCTION RECORD VERIFICATION ===")
for p in products:
    print(
        p.product_code,
        "| ID:", p.id,
        "|", p.name,
        "| size:", p.shape or "[read from description]",
        "| material:", p.material or "[not set]",
        "| finish:", p.finish or "[not set]",
        "| price:", p.price,
        "| stock:", p.stock,
    )
