"""
Signals API V1 custom serializer fields.
"""
from collections import OrderedDict

from rest_framework import serializers
from rest_framework.reverse import reverse

from signals.apps.signals.models import SubCategory


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

        # Tricking DRF to use API version `v1` because our `sub-category-detail` view lives in API
        # version 1. Afterwards we revert back to the origional API version from the request.
        original_version = request.version
        request.version = 'v1'
        url = reverse(view_name, kwargs=url_kwargs, request=request, format=format)
        request.version = original_version

        return url

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


class PrivateSignalLinksFieldWithArchives(serializers.HyperlinkedIdentityField):

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(href=self.get_url(value, "private-signals-detail", request, None))),
            ('archives', dict(href=self.get_url(value, "private-signals-history", request, None))),
            ('image', dict(href=self.get_url(value, "private-signals-image", request, None))),
        ])

        return result


class PrivateSignalLinksField(serializers.HyperlinkedIdentityField):

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(href=self.get_url(value, "private-signals-detail", request, None))),
        ])

        return result


class PublicSignalLinksField(serializers.HyperlinkedIdentityField):
    lookup_field = 'signal_id'

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(href=self.get_url(value, "public-signals-detail", request, None))),
        ])

        return result
