from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
content = path.read_text(encoding="utf-8")

# Use one consistent two-column specification table for every product.
table = r"""
<div class="product-specifications-table-wrap">
    <table class="product-specifications-table">
        <tbody>
            <tr>
                <th scope="row">Product Code</th>
                <td>{{ product.product_code|default:"Not assigned" }}</td>
            </tr>
            <tr>
                <th scope="row">Product Name</th>
                <td>{{ product.name|default:"Product" }}</td>
            </tr>
            <tr>
                <th scope="row">Category</th>
                <td>{{ product.category|default:"Not specified" }}</td>
            </tr>
            <tr>
                <th scope="row">Industry</th>
                <td>{{ product.industry|default:"Not specified" }}</td>
            </tr>
            <tr>
                <th scope="row">Ideal Material</th>
                <td>{{ product.material|default:"Confirm material for the intended application" }}</td>
            </tr>
            <tr>
                <th scope="row">Finish</th>
                <td>{{ product.finish|default:"Matte or Gloss, subject to product requirements" }}</td>
            </tr>
            <tr>
                <th scope="row">Standard Size</th>
                <td>{{ product.standard_size|default:product.size|default:"Confirm size when ordering" }}</td>
            </tr>
            <tr>
                <th scope="row">Adhesive</th>
                <td>{{ product.adhesive|default:"Confirm adhesive for the intended surface" }}</td>
            </tr>
            <tr>
                <th scope="row">Description</th>
                <td>{{ product.description|default:"Contact us for product details."|linebreaksbr }}</td>
            </tr>
            <tr>
                <th scope="row">Primary Application</th>
                <td>{{ product.primary_application|default:"Refer to the product description and intended use." }}</td>
            </tr>
            <tr>
                <th scope="row">Buyer's Notes</th>
                <td>{{ product.buyers_notes|default:"Confirm dimensions, surface compatibility, and installation requirements before ordering." }}</td>
            </tr>
        </tbody>
    </table>
</div>
"""

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
    .product-specifications-table th {
        width: 36%;
    }
}
</style>
"""

# Locate the existing Product Specifications heading.
heading = re.search(
    r"<h[1-6]\b[^>]*>\s*Product\s+Specifications\s*</h[1-6]>",
    content,
    re.IGNORECASE
)

if not heading:
    print("ERROR: Product Specifications heading was not found.")
    print("The original template has been left unchanged.")
    sys.exit(2)

# Replace the consecutive existing specification rows, preserving
# the rest of the product detail page and its other sections.
row_pattern = re.compile(
    r"(?:\s*<div\b[^>]*class\s*=\s*['\"][^'\"]*\bspec\b[^'\"]*['\"][^>]*>"
    r"[\s\S]*?</div>\s*)+",
    re.IGNORECASE
)

match = row_pattern.search(content, heading.end())

if not match:
    print("ERROR: Existing .spec rows were not found after the heading.")
    print("No template changes were saved.")
    sys.exit(3)

updated = content[:match.start()] + "\n" + table + "\n" + content[match.end():]

# Add the styling once, immediately before </head> where possible.
if "product-specifications-table-wrap" not in content:
    head_end = re.search(r"</head\s*>", updated, re.IGNORECASE)
    if head_end:
        updated = (
            updated[:head_end.start()]
            + css + "\n"
            + updated[head_end.start():]
        )
    else:
        updated = css + "\n" + updated

path.write_text(updated, encoding="utf-8")
print("Product Specifications table has been updated.")
print(f"Template: {path}")
