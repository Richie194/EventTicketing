from django import template

register = template.Library()

@register.filter
def dictkey(d, key):
    """Allows access to dictionary values by key in templates."""
    return d.get(key)
