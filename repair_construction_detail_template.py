from pathlib import Path
from datetime import datetime
import re
import shutil

template = Path("templates/products/product_detail.html")
source = template.read_text(encoding="utf-8")

start_marker = "                            {% if product.description %}"
end_marker = "                            {% endif %}"

# Find the specific description row labelled Description & Buyer Notes.
pattern = re.compile(
    r"(?P<indent>[ \t]*)\{% if product\.description %\}\s*"
    r"<tr>\s*"
    r"<th scope=\"row\">Description &amp; Buyer Notes</th>\s*"
    r"<td>\{\{ product\.description\|linebreaksbr \}\}</td>\s*"
    r"</tr>\s*"
    r"\{% endif %\}",
    re.MULTILINE
)

match = pattern.search(source)
if not match:
    raise RuntimeError(
        "Could not find the exact Description & Buyer Notes block. "
        "Template was not changed."
    )

replacement = r"""
                            {% if product.description %}
                                {% if product.industry == 'construction' and product.product_code|slice:":1" == 'C' %}
                                    <tr>
                                        <th scope="row">Description</th>
                                        <td>{{ product.description|cut:"Standard size:"|cut:"Primary application:"|cut:"Buyer's notes:"|linebreaksbr }}</td>
                                    </tr>
                                    {% if product.shape %}
                                    <tr>
                                        <th scope="row">Standard Size</th>
                                        <td>{{ product.shape }}</td>
                                    </tr>
                                    {% endif %}
                                    {% if product.material %}
                                    <tr>
                                        <th scope="row">Ideal Material</th>
                                        <td>{{ product.material }}</td>
                                    </tr>
                                    {% endif %}
                                    {% if product.finish %}
                                    <tr>
                                        <th scope="row">Finish</th>
                                        <td>{{ product.finish }}</td>
                                    </tr>
                                    {% endif %}
                                    <tr>
                                        <th scope="row">Primary Application</th>
                                        <td>
                                            {% if "Primary application:" in product.description %}
                                                {{ product.description|slice:"0:" }}
                                                {% with parts=product.description|cut:"Primary application:" %}
                                                {% endwith %}
                                                {{ product.description|linebreaksbr }}
                                            {% else %}
                                                See product description.
                                            {% endif %}
                                        </td>
                                    </tr>
                                    <tr>
                                        <th scope="row">Buyer's Notes</th>
                                        <td>
                                            {% if "Buyer's notes:" in product.description %}
                                                {{ product.description|linebreaksbr }}
                                            {% else %}
                                                Follow the product's application requirements and confirm specifications before printing.
                                            {% endif %}
                                        </td>
                                    </tr>
                                {% else %}
                                    <tr>
                                        <th scope="row">Description &amp; Buyer Notes</th>
                                        <td>{{ product.description|linebreaksbr }}</td>
                                    </tr>
                                {% endif %}
                            {% endif %}"""

# Back up first, then replace only the exact description block.
backup = template.with_name(
    "product_detail.before_construction_specs_" +
    datetime.now().strftime("%Y%m%d_%H%M%S") + ".html"
)
shutil.copy2(template, backup)
updated = source[:match.start()] + replacement + source[match.end():]

# Do not write an incomplete or suspicious result.
if updated == source:
    raise RuntimeError("No template changes were generated.")
template.write_text(updated, encoding="utf-8")
print("Template updated:", template)
print("Backup saved:", backup)
