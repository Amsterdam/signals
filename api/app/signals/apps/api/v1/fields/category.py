from collections import OrderedDict

from rest_framework import serializers
from rest_framework.reverse import reverse

from signals.apps.signals.models import Category


class ParentCategoryHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    lookup_field = 'slug'

    def to_representation(self, value):
        request = self.context.get('request')
        result = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request))),
            ('self', dict(href=self.get_url(value, 'category-detail', request, None))),
        ])

        return result


class CategoryHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):

    def get_url(self, obj, view_name, request, format):
        url_kwargs = {
            'slug': obj.parent.slug,
            'sub_slug': obj.slug,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    def to_representation(self, value):
        request = self.context.get('request')
        result = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request))),
            ('self', dict(href=self.get_url(value, 'category-detail', request, None))),
        ])

        return result


class CategoryHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
    view_name = 'category-detail'
    queryset = Category.objects.all()

    def to_internal_value(self, data):
        request = self.context.get('request', None)
        original_version = request.version

        # Tricking DRF to use API version `v1` because our `category-detail` view lives in API
        # version 1. Afterwards we revert back to the origional API version from the request.
        request.version = 'v1'
        value = super().to_internal_value(data)
        request.version = original_version

        return value

    def get_url(self, obj: Category, view_name, request, format):

        if obj.is_child():
            url_kwargs = {
                'slug': obj.parent.slug,
                'sub_slug': obj.slug,
            }
        else:
            url_kwargs = {
                'slug': obj.slug,
            }

        # Tricking DRF to use API version `v1` because our `category-detail` view lives in API
        # version 1. Afterwards we revert back to the origional API version from the request.
        original_version = request.version
        request.version = 'v1'
        url = reverse(view_name, kwargs=url_kwargs, request=request, format=format)
        request.version = original_version

        return url

    def get_object(self, view_name, view_args, view_kwargs):
        return self.get_queryset().get(
            parent__slug=view_kwargs['slug'],
            slug=view_kwargs['sub_slug'])
