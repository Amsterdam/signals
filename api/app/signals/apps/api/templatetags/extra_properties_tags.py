# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django import template
from django.conf import settings

register = template.Library()


@register.filter
def is_a_list(value):
    return isinstance(value, (list, tuple))


@register.filter
def get_extra_properties(signal):
    if not settings.FEATURE_FLAGS.get('API_FILTER_EXTRA_PROPERTIES', False):
        return signal.extra_properties

    category_url = signal.category_assignment.category.get_absolute_url()
    category_urls = [category_url, f'{category_url}/']
    if signal.category_assignment.category.is_child():
        parent_category_url = signal.category_assignment.category.parent.get_absolute_url()
        category_urls += [parent_category_url, f'{parent_category_url}/']

    return filter(lambda x: 'category_url' in x and x['category_url'] in category_urls, signal.extra_properties)
