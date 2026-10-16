from pathlib import Path
import ast
import re
import sys

path = Path("products/views.py")
source = path.read_text(encoding="utf-8-sig")
original = source

# Identify the actual industry-filter conditional without guessing line numbers.
tree = ast.parse(source, filename=str(path))
targets = []

for node in ast.walk(tree):
    if not isinstance(node, ast.If):
        continue

    test = node.test
    if isinstance(test, ast.Name) and test.id == "industry_filter":
        targets.append(node)

if len(targets) != 1:
    raise RuntimeError(
        f"Expected exactly one 'if industry_filter:' block; found {len(targets)}. "
        "No source changes have been made."
    )

node = targets[0]
lines = source.splitlines()
indent = re.match(r"^[ \t]*", lines[node.lineno - 1]).group(0)
inner = indent + "    "

replacement_lines = [
    indent + "if industry_filter:",
    inner + "    from django.db.models import Q",
    inner + "    filter_key = str(industry_filter).strip().lower()",
    inner + "    filter_key = filter_key.replace(' ', '_').replace('-', '_')",
    inner + "    matching_industries = industry_aliases.get(",
    inner + "        filter_key, industry_aliases.get(industry_filter, [industry_filter])",
    inner + "    )",
    inner + "    category_query = Q()",
    inner + "    for category_value in set([filter_key, *matching_industries]):",
    inner + "        if category_value:",
    inner + "            category_query |= Q(category__iexact=str(category_value))",
    inner + "    industry_query = Q(industry__in=matching_industries)",
    inner + "    # Exclude known legacy misclassifications from the industry match.",
    inner + "    # The category match remains available for a correctly classified product.",
    inner + "    if filter_key in ('waste', 'waste_companies'):",
    inner + "        industry_query &= ~Q(product_code__in=['G007', 'G012', 'P002', 'P007'])",
    inner + "    elif filter_key in ('construction', 'construction_contractors'):",
    inner + "        industry_query &= ~Q(product_code__in=['G013', 'P003'])",
    inner + "    catalogue_query = category_query | industry_query",
    inner + "    # Include existing numbered series even when legacy category fields are wrong.",
    inner + "    if filter_key in ('pool', 'pools', 'pool_companies'):",
    inner + "        catalogue_query |= Q(product_code__regex=r'^P[0-9]+$')",
    inner + "    elif filter_key in ('government', 'government_contractor', 'government_contractors'):",
    inner + "        catalogue_query |= Q(product_code__regex=r'^G[0-9]+$')",
    inner + "    elif filter_key in ('construction', 'construction_contractors'):",
    inner + "        catalogue_query |= Q(product_code__regex=r'^C[0-9]+$')",
    inner + "    products = products.filter(catalogue_query).distinct()",
]

replacement = "\n".join(replacement_lines)

# Replace only the located conditional, preserving the rest of the view.
updated_lines = (
    lines[:node.lineno - 1]
    + replacement.splitlines()
    + lines[node.end_lineno:]
)
updated = "\n".join(updated_lines) + ("\n" if source.endswith("\n") else "")

# Validate syntax before writing anything.
compile(updated, str(path), "exec")

# Make sure the Shippo checkout and shipment-related code was not removed.
for required in ("get_shippo_shipping_rates", "industry_filter"):
    if required not in updated:
        raise RuntimeError(f"Safety validation failed: {required} is missing.")

path.write_text(updated, encoding="utf-8")
print("Catalogue filters updated and Python syntax validated.")
print("Future products can appear through matching category or industry fields.")
print("Existing P/G/C numbered product series are supported without a 20-item cap.")
