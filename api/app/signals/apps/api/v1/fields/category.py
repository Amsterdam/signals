from collections import OrderedDict

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_extensions.settings import extensions_api_settings

from signals.apps.api.v1.fields.decorators import enforce_request_version_v1
from signals.apps.signals.models import Category


def category_public_url(category, request, format=None):
    if category.is_child():
        viewname, kwargs = 'public-subcategory-detail', {'parent_lookup_parent__slug': category.parent.slug,
                                                         'slug': category.slug}
    else:
        viewname, kwargs = 'public-maincategory-detail', {'slug': category.slug}
    return reverse(viewname, kwargs=kwargs, request=request, format=format)


class CategoryHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    def to_representation(self, value):
        request = self.context.get('request')
        result = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request))),
            ('self', {'href': category_public_url(value, request)}),
        ])
        return result


class CategoryHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
    view_name = 'public-subcategory-detail'
    queryset = Category.objects.all()
    parent_lookup_prefix = extensions_api_settings.DEFAULT_PARENT_LOOKUP_KWARG_NAME_PREFIX

    def get_object(self, view_name, view_args, view_kwargs):
        queryset = self.get_queryset()
        if f'{self.parent_lookup_prefix}parent__slug' in view_kwargs:
            queryset = queryset.filter(parent__slug=view_kwargs[f'{self.parent_lookup_prefix}parent__slug'])
        return queryset.get(slug=view_kwargs['slug'])

    def get_url(self, obj, view_name, request, format):
        # We want a Category instance, DRF can also return a PKOnlyObject when use_pk_only_optimization is enabled
        category = obj if isinstance(obj, Category) else self.get_queryset().get(pk=obj.pk)
        return category_public_url(category, request=request, format=format)

    @enforce_request_version_v1
    def to_internal_value(self, data):
        return super(CategoryHyperlinkedRelatedField, self).to_internal_value(data=data)


class PrivateCategoryHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    def _get_public_url(self, obj, request=None):
        return category_public_url(obj, request=request)

    def _get_status_message_templates_url(self, obj, request=None):
        if obj.is_child():
            viewname, kwargs = 'private-status-message-templates-child', {'slug': obj.parent.slug, 'sub_slug': obj.slug}
        else:
            viewname, kwargs = 'private-status-message-templates-parent', {'slug': obj.slug}
        return self.reverse(viewname, kwargs=kwargs, request=request)

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
