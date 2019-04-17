from django import template

register = template.Library()


@register.simple_tag
def translate_value(value):
    if isinstance(value, bool):
        return 'Ja' if value else 'Nee'
    if value is None:
        return '-'
    return value
