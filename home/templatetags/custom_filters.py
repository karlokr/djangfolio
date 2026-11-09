import json

from django import template
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='replace')
def replace(value, args):
    """
    Replace occurrences of a string with another string.
    Usage: {{ value|replace:"old,new" }}
    Example: {{ email|replace:"@, [@] " }}
    """
    if not args or ',' not in args:
        return value
    
    old, new = args.split(',', 1)
    return value.replace(old, new)


@register.filter(name='seo_description')
def seo_description(value, limit=160):
    """
    Plain-text summary for a meta description, at most ``limit`` characters.
    Tags are stripped and whitespace collapsed; a longer text is cut at the
    last word boundary and ends with an ellipsis, rather than mid-word.
    Usage: {{ post.excerpt|seo_description }}
    """
    text = ' '.join(strip_tags(str(value or '')).split())
    limit = int(limit)
    if len(text) <= limit:
        return text
    cut = text[:limit - 1]
    if ' ' in cut:
        cut = cut[:cut.rindex(' ')]
    return cut.rstrip(' ,;:.-–—') + '…'


_JSON_ESCAPES = {ord('<'): '\\u003C', ord('>'): '\\u003E', ord('&'): '\\u0026'}


@register.filter(name='json_ld')
def json_ld(items):
    """
    A JSON-LD document from a list of schema.org objects, safe inside
    <script type="application/ld+json"> (<, > and & are escaped, so text
    can't close the script element).
    Usage: <script type="application/ld+json">{{ structured_data|json_ld }}</script>
    """
    document = {'@context': 'https://schema.org', '@graph': list(items)}
    return mark_safe(json.dumps(document, ensure_ascii=False).translate(_JSON_ESCAPES))

