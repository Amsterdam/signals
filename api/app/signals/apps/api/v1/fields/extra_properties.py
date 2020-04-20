from django.conf import settings
from rest_framework.fields import JSONField

from signals.apps.api.ml_tool.utils import url_from_category


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

        # SIG-1711: Only show extra properties that belong to the currently assigned category or
        #           the parent of the currently assigned category
        category = self.instance.category_assignment.category
        category_urls = [url_from_category(category), ]
        if category.is_child():
            category_urls.append(url_from_category(category.parent))

        return filter(
            lambda x: 'category_url' in x and x['category_url'] in category_urls, representation
        )
