from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path.cwd()
VIEWS = ROOT / "staff" / "views.py"
STAFF_TEMPLATES = ROOT / "staff" / "templates"
PRODUCT_TEMPLATES = ROOT / "products" / "templates"
BACKUP = ROOT / sys.argv[1]
changed = []

def save_and_write(path, content):
    if path.read_text(encoding="utf-8") == content:
        return
    rel = path.relative_to(ROOT)
    target = BACKUP / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    path.write_text(content, encoding="utf-8")
    changed.append(str(rel))

# 1. Fix dashboard context names and missing dashboard data.
source = VIEWS.read_text(encoding="utf-8")
start = source.find("def staff_dashboard(request):")
end = source.find("\ndef ", start + 5)
if start < 0 or end < 0:
    raise RuntimeError("Could not safely locate staff_dashboard in staff/views.py.")

section = source[start:end]
if '"total_products":' not in section:
    marker = '    context = {\n'
    if marker not in section:
        raise RuntimeError("Dashboard context block was not found; no dashboard edits were made.")

    addition = '''    recent_quotes = QuoteRequest.objects.order_by("-created_at")[:8]
    recent_activity = StaffActivityLog.objects.select_related(
        "staff", "staff__user"
    ).order_by("-id")[:8]

    approved_staff_count = StaffProfile.objects.filter(
        approved=True, status="approved"
    ).count()
    pending_staff_count = StaffProfile.objects.exclude(
        approved=True, status="approved"
    ).count()

'''
    section = section.replace(marker, addition + marker, 1)

    # Keep existing context entries and add aliases expected by dashboard.html.
    alias_block = '''        "total_products": products_count,
        "available_products": available_products_count,
        "total_orders": orders_count,
        "total_quotes": quotes_count,
        "new_quotes": new_quotes_count,
        "reviewing_quotes": reviewing_quotes_count,
        "quoted_quotes": quoted_count,
        "approved_quotes": approved_quotes_count,
        "production_quotes": in_production_count,
        "completed_quotes": completed_quotes_count,
        "approved_staff": approved_staff_count,
        "pending_staff": pending_staff_count,
        "recent_quotes": recent_quotes,
        "recent_activity": recent_activity,
'''
    section = section.replace(marker, marker + alias_block, 1)
    source = source[:start] + section + source[end:]
    save_and_write(VIEWS, source)
    print("FIXED: dashboard context names and data")
else:
    print("SKIPPED: dashboard aliases already exist")

# 2. Replace outdated branding only in staff templates.
if STAFF_TEMPLATES.exists():
    for path in STAFF_TEMPLATES.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".txt"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        updated = content
        updated = re.sub(r"SwiftCart Staff Portal", "THE LABEL GROUP STAFF PORTAL", updated, flags=re.I)
        updated = re.sub(r"SwiftCart Staff", "THE LABEL GROUP STAFF", updated, flags=re.I)
        updated = re.sub(r"SwiftCart", "THE LABEL GROUP", updated, flags=re.I)
        if updated != content:
            save_and_write(path, updated)
            print("BRANDING:", path.relative_to(ROOT))

# 3. Add a specification table to a clearly named product-detail template,
#    using only fields that actually exist on the Product model.
if PRODUCT_TEMPLATES.exists():
    candidates = [
        p for p in PRODUCT_TEMPLATES.rglob("*.html")
        if "detail" in p.name.lower()
    ]
    inserted = False
    table = '''
<section class="product-specifications" style="margin:24px 0;">
  <h2>Product Specifications</h2>
  <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;">
      <tbody>
        {% if product.product_code %}<tr><th style="text-align:left;padding:10px;border:1px solid #ddd;">Product Code</th><td style="padding:10px;border:1px solid #ddd;">{{ product.product_code }}</td></tr>{% endif %}
        {% if product.product_type %}<tr><th style="text-align:left;padding:10px;border:1px solid #ddd;">Product Type</th><td style="padding:10px;border:1px solid #ddd;">{{ product.get_product_type_display|default:product.product_type }}</td></tr>{% endif %}
        {% if product.category %}<tr><th style="text-align:left;padding:10px;border:1px solid #ddd;">Category</th><td style="padding:10px;border:1px solid #ddd;">{{ product.category }}</td></tr>{% endif %}
        {% if product.industry %}<tr><th style="text-align:left;padding:10px;border:1px solid #ddd;">Industry</th><td style="padding:10px;border:1px solid #ddd;">{{ product.industry }}</td></tr>{% endif %}
        {% if product.brand %}<tr><th style="text-align:left;padding:10px;border:1px solid #ddd;">Brand</th><td style="padding:10px;border:1px solid #ddd;">{{ product.brand }}</td></tr>{% endif %}
        {% if product.material %}<tr><th style="text-align:left;padding:10px;border:1px solid #ddd;">Material</th><td style="padding:10px;border:1px solid #ddd;">{{ product.material }}</td></tr>{% endif %}
        {% if product.finish %}<tr><th style="text-align:left;padding:10px;border:1px solid #ddd;">Finish</th><td style="padding:10px;border:1px solid #ddd;">{{ product.finish }}</td></tr>{% endif %}
        {% if product.shape %}<tr><th style="text-align:left;padding:10px;border:1px solid #ddd;">Shape</th><td style="padding:10px;border:1px solid #ddd;">{{ product.shape }}</td></tr>{% endif %}
        {% if product.printing_method %}<tr><th style="text-align:left;padding:10px;border:1px solid #ddd;">Printing Method</th><td style="padding:10px;border:1px solid #ddd;">{{ product.printing_method }}</td></tr>{% endif %}
        {% if product.adhesive %}<tr><th style="text-align:left;padding:10px;border:1px solid #ddd;">Adhesive</th><td style="padding:10px;border:1px solid #ddd;">{{ product.adhesive }}</td></tr>{% endif %}
        {% if product.description %}<tr><th style="text-align:left;padding:10px;border:1px solid #ddd;">Description</th><td style="padding:10px;border:1px solid #ddd;">{{ product.description|linebreaksbr }}</td></tr>{% endif %}
      </tbody>
    </table>
  </div>
</section>
'''
    for path in candidates:
        content = path.read_text(encoding="utf-8")
        if "Product Specifications" in content:
            print("SKIPPED: specification table already present in", path.relative_to(ROOT))
            inserted = True
            break
        if re.search(r"\bproduct\.description\b|\bproduct\.name\b", content):
            # Insert before the final block terminator, preserving the template structure.
            position = content.rfind("{% endblock")
            if position >= 0:
                updated = content[:position] + table + "\n" + content[position:]
                save_and_write(path, updated)
                print("ADDED: product specification table to", path.relative_to(ROOT))
                inserted = True
                break
    if not inserted:
        print("NOTE: No recognised product-detail template was changed.")
        print("The dashboard and branding fixes can still be applied.")

# Verify Python syntax and Django configuration.
result = subprocess.run(
    [sys.executable, "manage.py", "check"],
    cwd=ROOT, text=True, capture_output=True
)
print("\n===== DJANGO CHECK =====")
print(result.stdout)
if result.stderr:
    print(result.stderr)
if result.returncode != 0:
    print("Django check failed. Restoring changed files from backup.")
    for item in reversed(changed):
        original = BACKUP / item
        destination = ROOT / item
        if original.exists():
            shutil.copy2(original, destination)
    sys.exit(result.returncode)

print("\n===== RESULT =====")
print("Changed files:", len(changed))
for item in changed:
    print(" -", item)
print("Backup folder:", BACKUP)
print("Database records were not deleted or recreated.")
