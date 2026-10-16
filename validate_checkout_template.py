import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swiftcart.settings")
import django
django.setup()
from django.template.loader import get_template
get_template("checkout.html")
print("Checkout template loaded successfully.")
