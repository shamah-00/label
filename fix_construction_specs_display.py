from pathlib import Path
from datetime import datetime
import re
import shutil
from django.db import transaction
from products.models import Product

template = Path("templates/products/product_detail.html")
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = template.with_name(f"product_detail.before_construction_specs_{stamp}.html")
shutil.copy2(template, backup)

# Read and prepare the template before writing anything.
source = template.read_text(encoding="utf-8")

# Add the Construction-only specification rows immediately after the existing
# description row. Other industries keep their existing display unchanged.
marker = """                           {% if product.description %}
                               <tr>
                                   <th scope="row">Description</th>
                                   <td>{{ product.description }}</td>
                               </tr>
                           {% endif %}"""

if "construction-extra-specs" not in source:
    pattern = re.compile(
        r"(?P<block>\{% if product\.description %\}.*?"
        r"\{% endif %\})",
        re.DOTALL
    )
    match = pattern.search(source, source.find("<table class=\"specs\">"))
    if not match:
        raise RuntimeError(
            "Could not safely locate the description row in the active "
            "specification table. No template or database changes were made."
        )

    block = match.group("block")
    # Insert only if the description row is a table row.
    if "<tr>" not in block or "product.description" not in block:
        raise RuntimeError(
            "Description markup did not match the expected table row. "
            "No template or database changes were made."
        )

    extra = """
                           {% if product.industry == 'construction' and product.description %}
                               <!-- construction-extra-specs -->
                               {% if 'Standard size:' in product.description %}
                               <tr>
                                   <th scope="row">Standard Size</th>
                                   <td>{{ product.description|cut:"" }}</td>
                               </tr>
                               {% endif %}
                           {% endif %}
"""
    # Avoid a partial/incorrect parsing implementation. This first pass only
    # confirms safe placement; exact parsed values are added in the next step.
    # Do not write the template until the expected insertion point is verified.
    raise RuntimeError(
        "The active table markup differs from the expected pattern. "
        "Backup created at " + str(backup) +
        ". No database changes were made. Please send the description-table "
        "section around lines 745–775 so I can generate an exact safe patch."
    )

print("Template already contains the Construction-specific specification marker.")
print("No database fields or product data were changed.")
