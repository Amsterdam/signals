from django import template
from django.conf import settings

from signals.apps.api.ml_tool.utils import url_from_category

register = template.Library()


@register.filter
def is_a_list(value):
    return isinstance(value, (list, tuple))


@register.filter
def get_extra_properties(signal):
    if not settings.FEATURE_FLAGS.get('API_FILTER_EXTRA_PROPERTIES', False):
        return signal.extra_properties

    category_url = url_from_category(signal.category_assignment.category)
    category_urls = [category_url, f'{category_url}/']
    if signal.category_assignment.category.is_child():
        category_url = url_from_category(signal.category_assignment.category.parent)
        category_urls += [category_url, f'{category_url}/']

    return filter(lambda x: 'category_url' in x and x['category_url'] in category_urls, signal.extra_properties)
