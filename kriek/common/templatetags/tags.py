
from django import template

register = template.Library()

@register.simple_tag
def active(request, pattern, pk=""):
    import re
    if re.search(pattern+str(pk), request.path):
        return 'active'
    return ''