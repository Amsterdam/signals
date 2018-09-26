from collections import OrderedDict

from rest_framework import serializers
from rest_framework.reverse import reverse


class SignalLinksField(serializers.HyperlinkedIdentityField):
    """
    Return authorized url. handy for development.
    """

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(
                href=self.get_url(value, "signal-auth-detail", request, None))
             ),
        ])

        return result


class SignalUnauthenticatedLinksField(serializers.HyperlinkedIdentityField):
    """
    Return url based on UUID instead of normal database id
    """
    lookup_field = 'signal_id'


class StatusLinksField(serializers.HyperlinkedIdentityField):
    """
    Return authorized url. handy for development.
    """

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(
                href=self.get_url(value, "status-auth-detail", request, None))
             ),
        ])

        return result


class CategoryLinksField(serializers.HyperlinkedIdentityField):

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(
                href=self.get_url(value, "category-auth-detail", request, None))
             ),
        ])

        return result


class PriorityLinksField(serializers.HyperlinkedIdentityField):

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(href=self.get_url(value, 'priority-auth-detail', request, None))),
        ])

        return result


class MainCategoryLinksField(serializers.HyperlinkedIdentityField):
    lookup_field = 'slug'

    def to_representation(self, value):
        request = self.context.get('request')
        result = OrderedDict([
            ('self', dict(href=self.get_url(value, 'category-detail', request, None))),
        ])

        return result


class SubCategoryLinksField(serializers.HyperlinkedIdentityField):

    def get_url(self, obj, view_name, request, format):
        url_kwargs = {
            'slug': obj.main_category.slug,
            'sub_slug': obj.slug,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    def to_representation(self, value):
        request = self.context.get('request')
        result = OrderedDict([
            ('self', dict(href=self.get_url(value, 'sub-category-detail', request, None))),
        ])

        return result
