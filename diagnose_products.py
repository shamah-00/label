import inspect
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse, resolve
from django.template.loader import get_template

print("\n========== ACTIVE PRODUCT VIEWS ==========")

import staff.views as views

for name in ("staff_products", "staff_product_add", "staff_product_edit"):
    fn = getattr(views, name, None)
    print(f"\n--- {name} ---")
    if fn:
        print(inspect.getsource(fn))
    else:
        print("ERROR: View function is missing")

print("\n========== PRODUCT MODEL ==========")
try:
    from products.models import Product
    print("Product model:", Product)
    print("Fields:", [f.name for f in Product._meta.fields])
    print("Product count:", Product.objects.count())
except Exception as exc:
    print("MODEL ERROR:", repr(exc))

print("\n========== PRODUCT FORM IMPORTS ==========")
for module_name in ("staff.forms", "products.forms"):
    try:
        module = __import__(module_name, fromlist=["*"])
        print(f"\n{module_name}:")
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if "product" in name.lower() and hasattr(obj, "is_valid"):
                print(name, inspect.getfile(obj))
    except Exception as exc:
        print(module_name, "ERROR:", repr(exc))

print("\n========== TEMPLATES ==========")
for name in (
    "staff/products/list.html",
    "staff/products/form.html",
    "staff/products/edit.html",
):
    try:
        print(name, "OK:", get_template(name).origin.name)
    except Exception as exc:
        print(name, "ERROR:", repr(exc))

print("\n========== AUTHENTICATED PAGE TESTS ==========")
User = get_user_model()
user = User.objects.filter(username="amos").first()

if not user:
    print("ERROR: User 'amos' was not found.")
else:
    print("Username:", user.username, "| Active:", user.is_active,
          "| Staff:", user.is_staff, "| Superuser:", user.is_superuser)

    client = Client(raise_request_exception=False)
    client.force_login(user)

    for name in ("staff_products", "staff_product_add"):
        try:
            url = reverse(name)
            response = client.get(url)
            print(f"\n{name}: {url}")
            print("HTTP STATUS:", response.status_code)
            print("REDIRECT:", response.get("Location", "None"))
            if response.status_code >= 400:
                print("RESPONSE:", response.content.decode(
                    "utf-8", errors="replace"
                )[:2500])
            else:
                print("TEMPLATE:", [
                    t.name for t in getattr(response, "templates", [])
                ])
        except Exception as exc:
            print(name, "ERROR:", repr(exc))

print("\n========== END DIAGNOSTIC ==========")
