from pathlib import Path
import re

path = Path(r"staff/templates/staff/products/form.html")
content = path.read_text(encoding="utf-8-sig")

pattern = re.compile(
    r'{%\s*url\s+(["\'])staff_product_image_delete\1\s+([^%]+?)\s*%}'
)

replacement = r'{% if product and product.pk %}{% url "staff_product_image_delete" \2 %}{% endif %}'
updated, count = pattern.subn(replacement, content)

if count:
    path.write_text(updated, encoding="utf-8")
    print(f"Fixed {count} image-delete URL tag(s).")
    print("Backup: staff/templates/staff/products/form.html.before-image-url-fix")
else:
    print("No matching URL tag was found. The template was not changed.")
    for line_no, line in enumerate(content.splitlines(), 1):
        if "staff_product_image_delete" in line:
            print(f"Line {line_no}: {line.strip()}")
