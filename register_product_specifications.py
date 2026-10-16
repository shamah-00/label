from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8-sig")

# Register the tag library explicitly so Django can find it even if
# automatic app discovery is not working.
if re.search(r"""['"]product_specifications['"]\s*:""", text):
    print("An explicit product_specifications mapping already exists.")
else:
    match = re.search(r"""(['"])OPTIONS\1\s*:\s*\{""", text)
    if not match:
        raise SystemExit(
            "Could not safely locate OPTIONS inside TEMPLATES in settings.py. "
            "No settings change made."
        )

    insertion = (
        match.group(0)
        + "\n            'libraries': {\n"
        + "                'product_specifications': "
        + "'products.templatetags.product_specifications',\n"
        + "            },"
    )
    text = text[:match.start()] + insertion + text[match.end():]
    path.write_text(text, encoding="utf-8")
    print("Registered product_specifications in TEMPLATES OPTIONS.")
