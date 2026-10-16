import re
import html
from django import template
from django.utils.html import strip_tags

register = template.Library()

LABELS = [
    "Description",
    "Standard Size",
    "Ideal Material",
    "Finish",
    "Adhesive",
    "Primary Application",
    "What to Include / Buyer's Notes",
    "Buyer's Notes",
    "Buyer Notes",
]

LABEL_PATTERN = re.compile(
    r"(?<!\w)("
    + "|".join(re.escape(label) for label in sorted(LABELS, key=len, reverse=True))
    + r")\s*:?",
    re.IGNORECASE,
)

def extract_sections(value):
    if not value:
        return {}

    # Preserve boundaries between HTML line breaks before stripping tags.
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", str(value), flags=re.I)
    text = re.sub(r"</\s*(p|div|li)\s*>", "\n", text, flags=re.I)
    text = html.unescape(strip_tags(text))
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)

    matches = list(LABEL_PATTERN.finditer(text))
    sections = {}

    for index, match in enumerate(matches):
        label = re.sub(r"\s+", " ", match.group(1)).strip().lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)

        value_text = text[start:end].strip(" \t\r\n:;")
        value_text = re.sub(r"\n\s*\n+", "\n", value_text).strip()

        if label in ("what to include / buyer's notes", "buyer's notes", "buyer notes"):
            key = "buyers_notes"
        else:
            key = label.replace(" ", "_")

        if value_text:
            sections[key] = value_text

    # If no labelled sections were found, retain the full description.
    if not sections:
        cleaned = text.strip()
        if cleaned:
            sections["description"] = cleaned

    return sections

@register.filter
def spec_part(value, part_name):
    sections = extract_sections(value)
    key = re.sub(r"\s+", "_", str(part_name).strip().lower())
    if key in ("what_to_include_/_buyer's_notes", "buyer's_notes", "buyer_notes"):
        key = "buyers_notes"
    return sections.get(key, "")

@register.filter
def spec_plain(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", html.unescape(strip_tags(str(value)))).strip()
