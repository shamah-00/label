from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
content = path.read_text(encoding="utf-8-sig")

heading = re.search(
    r"<h[1-6]\b[^>]*>\s*Product\s+Specifications\s*</h[1-6]>",
    content,
    re.IGNORECASE
)
if not heading:
    raise SystemExit("Product Specifications heading not found; template unchanged.")

tail = content[heading.end():]
table = re.search(r"<table\b[^>]*>[\s\S]*?</table\s*>", tail, re.IGNORECASE)
if not table:
    raise SystemExit("Specifications table not found after heading; template unchanged.")

start = heading.end() + table.start()
end = heading.end() + table.end()

new_table = r"""
<div class="product-specifications-table-wrap">
    <table class="product-specifications-table">
        <tbody>
            <tr><th scope="row">Product Code</th><td>{{ product.product_code|default:"Not assigned" }}</td></tr>
            <tr><th scope="row">Product Name</th><td>{{ product.name|default:"Product" }}</td></tr>
            <tr><th scope="row">Category</th><td>{{ product.get_category_display|default:product.category|default:"Not specified" }}</td></tr>
            <tr><th scope="row">Industry</th><td>{{ product.get_industry_display|default:product.industry|default:"Not specified" }}</td></tr>
            <tr><th scope="row">Ideal Material</th><td>{{ product.description|spec_part:"Ideal Material"|default:product.material|default:"Confirm material for the intended application" }}</td></tr>
            <tr><th scope="row">Finish</th><td>{{ product.description|spec_part:"Finish"|default:product.finish|default:"Confirm finish when ordering" }}</td></tr>
            <tr><th scope="row">Standard Size</th><td>{{ product.description|spec_part:"Standard Size"|default:product.standard_size|default:product.size|default:"Confirm size when ordering" }}</td></tr>
            <tr><th scope="row">Adhesive</th><td>{{ product.description|spec_part:"Adhesive"|default:product.adhesive|default:"Confirm adhesive for the intended surface" }}</td></tr>
            <tr><th scope="row">Description</th><td>{{ product.description|spec_part:"Description"|default:product.description|spec_plain|default:"Contact us for product details." }}</td></tr>
            <tr><th scope="row">Primary Application</th><td>{{ product.description|spec_part:"Primary Application"|default:product.primary_application|default:"Refer to the product's intended use." }}</td></tr>
            <tr><th scope="row">Buyer's Notes</th><td>{{ product.description|spec_part:"What to Include / Buyer's Notes"|default:product.description|spec_part:"Buyer's Notes"|default:product.buyers_notes|default:"Confirm dimensions, surface compatibility, and installation requirements before ordering." }}</td></tr>
        </tbody>
    </table>
</div>
"""

updated = content[:start] + new_table + content[end:]

if "{% load product_specifications %}" not in updated:
    extends = re.search(r"{%\s*extends\b[^%]*%}", updated)
    if extends:
        updated = (
            updated[:extends.end()]
            + "\n{% load product_specifications %}"
            + updated[extends.end():]
        )
    else:
        updated = "{% load product_specifications %}\n" + updated

css = r"""
<style>
.product-specifications-table-wrap {
    width: 100%;
    max-width: 100%;
    margin: 18px 0 28px;
    overflow-x: auto;
    border: 1px solid #dce2e9;
    border-radius: 8px;
    background: #fff;
}
.product-specifications-table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    font-size: 14px;
    line-height: 1.65;
}
.product-specifications-table th,
.product-specifications-table td {
    padding: 13px 16px;
    border-bottom: 1px solid #e3e7ed;
    text-align: left;
    vertical-align: top;
    overflow-wrap: anywhere;
}
.product-specifications-table th {
    width: 25%;
    color: #0b1f3a;
    font-weight: 800;
    background: #f3f6f9;
}
.product-specifications-table td {
    color: #273444;
    background: #fff;
}
.product-specifications-table tr:last-child th,
.product-specifications-table tr:last-child td {
    border-bottom: 0;
}
@media (max-width: 600px) {
    .product-specifications-table th,
    .product-specifications-table td {
        padding: 10px;
        font-size: 13px;
    }
    .product-specifications-table th { width: 36%; }
}
</style>
"""

if "product-specifications-table-wrap" not in content:
    head = re.search(r"</head\s*>", updated, re.IGNORECASE)
    if head:
        updated = updated[:head.start()] + css + "\n" + updated[head.start():]
    else:
        updated = css + "\n" + updated

path.write_text(updated, encoding="utf-8")
print("Active product detail template updated:", path)
print("Specifications rows: 11")
