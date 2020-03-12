from collections import OrderedDict

from rest_framework import serializers
from rest_framework.reverse import reverse

from signals.apps.api.generics.relations import (
    ParameterisedHyperLinkedIdentityField,
    ParameterisedHyperlinkedRelatedField
)
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


class CategoryHyperlinkedIdentityField(ParameterisedHyperLinkedIdentityField):
    lookup_fields = (('parent.slug', 'slug'), ('slug', 'sub_slug'),)

    def to_representation(self, value):
        request = self.context.get('request')
        hyperlink = super(ParameterisedHyperlinkedRelatedField, self).to_representation(value=value)
        result = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request))),
            ('self', {'href': hyperlink})
        ])

        return result


class CategoryHyperlinkedRelatedField(ParameterisedHyperlinkedRelatedField):
    lookup_fields = (('parent.slug', 'slug'), ('slug', 'sub_slug'),)

    view_name = 'category-detail'
    queryset = Category.objects.all()


class LegacyCategoryHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
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


class PrivateCategoryHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    def _get_public_url(self, obj, request=None):
        if obj.is_child():
            kwargs = {'slug': obj.parent.slug, 'sub_slug': obj.slug}
        else:
            kwargs = {'slug': obj.slug}
        return self.reverse('category-detail', kwargs=kwargs, request=request)

    def _get_status_message_templates_url(self, obj, request=None):
        if obj.is_child():
            kwargs = {'slug': obj.parent.slug, 'sub_slug': obj.slug}
            return self.reverse('private-status-message-templates-child', kwargs=kwargs, request=request)
        else:
            kwargs = {'slug': obj.slug}
            return self.reverse('private-status-message-templates-parent', kwargs=kwargs, request=request)

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request))),
            ('self', dict(
                href=self.get_url(value, 'private-category-detail', request, None),
                public=self._get_public_url(obj=value, request=request),
             )),
            ('archives', dict(href=self.get_url(value, 'private-category-history', request, None))),
            ('sia:status-message-templates', dict(
                href=self._get_status_message_templates_url(obj=value, request=request)
            ))
        ])

        if value.is_child():
            result.update({'sia:parent': dict(
                href=self.get_url(value.parent, 'private-category-detail', request, None),
                public=self._get_public_url(obj=value.parent, request=request))
            })

        return result
