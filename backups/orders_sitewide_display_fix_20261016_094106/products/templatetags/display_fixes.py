from html import unescape
from django import template

register = template.Library()

@register.filter(name="decode_entities")
def decode_entities(value):
    """Decode HTML entities; Django will still escape the resulting text."""
    if value is None:
        return ""
    return unescape(str(value))
