from pathlib import Path
import re

tag_path = Path(r"products\templatetags\product_specifications.py")
template_path = Path(r"templates\products\product_detail.html")

parser_code = r"""
import re
from django import template

register = template.Library()

LABELS = [
    "What to Include / Buyer's Notes",
    "Primary Application",
    "Standard Size",
    "Ideal Material",
    "Buyer's Notes",
    "Description",
    "Adhesive",
    "Industry",
    "Finish",
]

LABEL_PATTERN = re.compile(
    r"(?<![A-Za-z])("
    + "|".join(re.escape(x) for x in sorted(LABELS, key=len, reverse=True))
    + r")\s*:",
    re.IGNORECASE,
)

def _clean(value):
    value = str(value or "").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    return value.strip(" \t\n:;")

def _matches(text):
    return list(LABEL_PATTERN.finditer(text or ""))

def _extract(text, wanted):
    text = str(text or "")
    wanted = re.sub(r"\s+", " ", str(wanted or "")).strip().lower()
    aliases = {
        "buyer's notes": {"buyer's notes", "what to include / buyer's notes"},
        "what to include / buyer's notes": {"buyer's notes", "what to include / buyer's notes"},
    }
    accepted = aliases.get(wanted, {wanted})
    matches = _matches(text)

    for index, match in enumerate(matches):
        label = re.sub(r"\s+", " ", match.group(1)).strip().lower()
        if label not in accepted:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        return _clean(text[match.end():end])

    return ""

def _notes_without_adhesive(text):
    notes = _extract(text, "What to Include / Buyer's Notes")
    if not notes:
        notes = _extract(text, "Buyer's Notes")

    # If adhesive details were stored inside the notes, display them
    # in the Adhesive row and leave the remaining notes here.
    sentences = re.split(r"(?<=[.!?])\s+", notes)
    remaining = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
        and not re.search(r"\badhesive\b", sentence, re.IGNORECASE)
    ]
    return _clean(" ".join(remaining))

@register.filter
def spec_part(value, label):
    text = str(value or "")
    wanted = re.sub(r"\s+", " ", str(label or "")).strip().lower()

    if wanted == "adhesive":
        explicit = _extract(text, "Adhesive")
        if explicit:
            return explicit

        notes = _extract(text, "What to Include / Buyer's Notes")
        if not notes:
            notes = _extract(text, "Buyer's Notes")

        sentences = re.split(r"(?<=[.!?])\s+", notes)
        for sentence in sentences:
            if re.search(r"\badhesive\b", sentence, re.IGNORECASE):
                return _clean(sentence)
        return ""

    if wanted in {"buyer's notes", "what to include / buyer's notes"}:
        return _notes_without_adhesive(text)

    return _extract(text, label)

@register.filter
def spec_plain(value):
    text = str(value or "")
    # Prefer the actual description field if it has an explicit label.
    description = _extract(text, "Description")
    if description:
        return description

    # Otherwise keep the introductory description and remove the
    # appended labelled specification fields.
    matches = _matches(text)
    if matches:
        text = text[:matches[0].start()]

    return _clean(text)
"""

template = template_path.read_text(encoding="utf-8-sig")

def replace_row(label, cell, source):
    global template
    pattern = re.compile(
        r'(<tr>\s*<th\s+scope="row"\s*>\s*'
        + re.escape(label)
        + r'\s*</th>\s*<td>).*?(</td>\s*</tr>)',
        re.IGNORECASE | re.DOTALL,
    )
    template, count = pattern.subn(
        lambda m: m.group(1) + cell + m.group(2),
        template,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"Could not uniquely update the '{label}' row.")

replace_row(
    "Ideal Material",
    '{{ product.description|spec_part:"Ideal Material"|default:product.material|default:"Confirm material for the intended application" }}',
    "",
)
replace_row(
    "Finish",
    '{{ product.description|spec_part:"Finish"|default:product.finish|default:"Confirm finish when ordering" }}',
    "",
)
replace_row(
    "Standard Size",
    '{{ product.description|spec_part:"Standard Size"|default:"Confirm size when ordering" }}',
    "",
)
replace_row(
    "Adhesive",
    '{{ product.description|spec_part:"Adhesive"|default:product.adhesive|default:"Confirm adhesive for the intended surface" }}',
    "",
)
replace_row(
    "Description",
    '{{ product.description|spec_part:"Description"|default:product.description|spec_plain|default:"Contact us for product details." }}',
    "",
)
replace_row(
    "Primary Application",
    '{{ product.description|spec_part:"Primary Application"|default:"Refer to the product intended use." }}',
    "",
)
replace_row(
    "Buyers Notes",
    '{{ product.description|spec_part:"What to Include / Buyer&#x27;s Notes"|default:product.description|spec_part:"Buyer&#x27;s Notes"|default:"Confirm dimensions, surface compatibility, and installation requirements before ordering." }}',
    "",
)

# The actual heading may contain a typographic apostrophe or ASCII apostrophe.
if "spec_part:" in template and "product.primary_application" in template:
    template = template.replace(
        '|default:product.primary_application',
        ''
    )
if "product.buyers_notes" in template:
    template = template.replace('|default:product.buyers_notes', '')

tag_path.write_text(parser_code.lstrip(), encoding="utf-8")
template_path.write_text(template, encoding="utf-8")
print("Updated shared specification parser and product detail template.")
