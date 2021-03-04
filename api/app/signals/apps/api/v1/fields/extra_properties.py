# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.conf import settings
from rest_framework.fields import JSONField


class SignalExtraPropertiesField(JSONField):
    def __init__(self, *args, **kwargs):
        self.instance = None
        super(SignalExtraPropertiesField, self).__init__(*args, **kwargs)

    def get_attribute(self, instance):
        self.instance = instance
        return instance.extra_properties

    def to_representation(self, value):
        representation = super(SignalExtraPropertiesField, self).to_representation(value=value)
        if not settings.FEATURE_FLAGS.get('API_FILTER_EXTRA_PROPERTIES', False):
            return representation

        category_url = self.instance.category_assignment.category.get_absolute_url()
        category_urls = [category_url, f'{category_url}/']
        if self.instance.category_assignment.category.is_child():
            parent_category_url = self.instance.category_assignment.category.parent.get_absolute_url()
            category_urls += [parent_category_url, f'{parent_category_url}/']

        return filter(
            lambda x: 'category_url' in x and x['category_url'] in category_urls, representation
        )
