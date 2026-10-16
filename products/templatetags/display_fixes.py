from html import unescape
from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name="decode_entities")
def decode_entities(value):
    """Decode text entities while keeping the resulting text HTML-safe."""
    if value is None:
        return ""
    decoded = unescape(str(value))
    return mark_safe(conditional_escape(decoded))
