from django import template

register = template.Library()


@register.simple_tag
def translate_value(value):
    if isinstance(value, bool):
        return 'Ja' if value else 'Nee'
    if not value:
        return '-'
    return value


@register.filter
def is_a_list(value):
    return isinstance(value, (list, tuple))
