from collections import OrderedDict

from rest_framework import serializers
from rest_framework.reverse import reverse

from signals.apps.signals.models import SubCategory


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


class MainCategoryHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    lookup_field = 'slug'

    def to_representation(self, value):
        request = self.context.get('request')
        result = OrderedDict([
            ('self', dict(href=self.get_url(value, 'category-detail', request, None))),
        ])

        return result


class SubCategoryHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):

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


class SubCategoryHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
    view_name = 'sub-category-detail'
    queryset = SubCategory.objects.all()

    def to_internal_value(self, data):
        request = self.context.get('request', None)
        origional_version = request.version

        # Tricking DRF to use API version `v1` because our `sub-category-detail` view lives in API
        # version 1. Afterwards we revert back to the origional API version from the request.
        request.version = 'v1'
        value = super().to_internal_value(data)
        request.version = origional_version

        return value

    def get_url(self, obj, view_name, request, format):
        url_kwargs = {
            'slug': obj.main_category.slug,
            'sub_slug': obj.slug,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    def get_object(self, view_name, view_args, view_kwargs):
        return self.get_queryset().get(
            main_category__slug=view_kwargs['slug'],
            slug=view_kwargs['sub_slug'])


class NoteHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(
                href=self.get_url(value, "note-auth-detail", request, None))
             ),
        ])

        return result
