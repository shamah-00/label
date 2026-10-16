from pathlib import Path
from datetime import datetime
import re
import shutil

views_path = Path("products/views.py")
template_path = Path("templates/products/product_detail.html")

if not views_path.exists() or not template_path.exists():
    raise RuntimeError("Could not find the expected view or active template.")

views = views_path.read_text(encoding="utf-8")
template = template_path.read_text(encoding="utf-8")

old_view = '''def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "products/product_detail.html", {'product': product})
'''

new_view = '''def product_detail(request, product_id):
    import re

    product = get_object_or_404(Product, id=product_id)
    context = {"product": product}

    # Extract the structured fields only for Construction catalogue products.
    code = str(getattr(product, "product_code", "") or "").upper()
    industry = str(getattr(product, "industry", "") or "").lower()

    if industry == "construction" and re.fullmatch(r"C\\d{3}", code):
        description = str(getattr(product, "description", "") or "")

        def extract_field(label):
            pattern = rf"(?im)^\\s*{re.escape(label)}:\\s*(.*?)\\s*$"
            match = re.search(pattern, description)
            return match.group(1).strip() if match else ""

        application = extract_field("Primary application")
        buyer_notes = extract_field("Buyer's notes")

        # Keep the descriptive paragraph, excluding the metadata lines.
        base_description = re.split(
            r"(?im)^\\s*(?:Standard size|Primary application|Buyer's notes):",
            description,
            maxsplit=1
        )[0].strip()

        context["construction_specs"] = {
            "description": base_description,
            "application": application,
            "buyer_notes": buyer_notes,
        }

    return render(request, "products/product_detail.html", context)
'''

if old_view not in views:
    raise RuntimeError(
        "The product_detail function did not match the expected version. "
        "No files were changed."
    )

# Locate the exact description section in the current active template.
lines = template.splitlines(keepends=True)
description_row = next(
    (i for i, line in enumerate(lines)
     if '<th scope="row">Description</th>' in line),
    None
)
legacy_row = next(
    (i for i, line in enumerate(lines)
     if "Description &amp; Buyer Notes" in line),
    None
)

if description_row is None or legacy_row is None or legacy_row <= description_row:
    raise RuntimeError(
        "Could not safely locate both description branches. No files changed."
    )

# Find the opening description conditional before the Construction branch.
start = None
for i in range(description_row, -1, -1):
    if "{% if product.description %}" in lines[i]:
        start = i
        break

if start is None:
    raise RuntimeError("Could not locate the description conditional.")

# Find the outer closing endif after the legacy row, before the table closes.
closing_candidates = [
    i for i in range(legacy_row, len(lines))
    if "{% endif %}" in lines[i]
]
table_end = next(
    (i for i in range(legacy_row, len(lines)) if "</tbody>" in lines[i]),
    None
)
if table_end is None:
    raise RuntimeError("Could not locate the specification table ending.")

closing_candidates = [i for i in closing_candidates if i < table_end]
if len(closing_candidates) < 2:
    raise RuntimeError(
        "Could not safely identify the description block boundaries."
    )

# The last endif before </tbody> closes the outer product.description condition.
end = closing_candidates[-1]

replacement = '''                            {% if product.description %}
                                {% if construction_specs %}
                                    <tr>
                                        <th scope="row">Description</th>
                                        <td>{{ construction_specs.description|default:"Product description not provided."|linebreaksbr }}</td>
                                    </tr>
                                    {% if construction_specs.application %}
                                    <tr>
                                        <th scope="row">Primary Application</th>
                                        <td>{{ construction_specs.application }}</td>
                                    </tr>
                                    {% endif %}
                                    {% if construction_specs.buyer_notes %}
                                    <tr>
                                        <th scope="row">Buyer's Notes</th>
                                        <td>{{ construction_specs.buyer_notes }}</td>
                                    </tr>
                                    {% endif %}
                                {% else %}
                                    <tr>
                                        <th scope="row">Description &amp; Buyer Notes</th>
                                        <td>{{ product.description|linebreaksbr }}</td>
                                    </tr>
                                {% endif %}
                            {% endif %}
'''.splitlines(keepends=True)

updated_template = "".join(lines[:start] + replacement + lines[end + 1:])

# For Construction products, label the existing shape/size row correctly.
updated_template = updated_template.replace(
    '<th scope="row">Shape</th>',
    '<th scope="row">{% if product.industry == "construction" and product.product_code|slice:":1" == "C" %}Standard Size{% else %}Shape{% endif %}</th>',
    1
)

# Verify before writing either file.
compile(new_view, str(views_path), "exec")
if updated_template == template:
    raise RuntimeError("Template update produced no changes.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
views_backup = views_path.with_name(f"views.before_construction_specs_{stamp}.py")
template_backup = template_path.with_name(
    f"product_detail.before_construction_specs_{stamp}.html"
)

shutil.copy2(views_path, views_backup)
shutil.copy2(template_path, template_backup)

views_path.write_text(views.replace(old_view, new_view, 1), encoding="utf-8")
template_path.write_text(updated_template, encoding="utf-8")

print("Updated:", views_path)
print("Updated:", template_path)
print("Backups:", views_backup, "and", template_backup)
print("Construction description parsing added.")
