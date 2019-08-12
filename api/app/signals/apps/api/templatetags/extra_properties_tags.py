from django import template

register = template.Library()


@register.filter
def is_a_list(value):
    return isinstance(value, (list, tuple))
