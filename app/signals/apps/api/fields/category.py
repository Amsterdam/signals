# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from collections import OrderedDict

from datapunt_api.serializers import LinksField
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_extensions.settings import extensions_api_settings

from signals.apps.signals.models import Category


def category_public_url(category, request, format=None):
    if category.is_child():
        viewname, kwargs = 'public-subcategory-detail', {'parent_lookup_parent__slug': category.parent.slug,
                                                         'slug': category.slug}
    else:
        viewname, kwargs = 'public-maincategory-detail', {'slug': category.slug}
    return reverse(viewname, kwargs=kwargs, request=request, format=format)


@extend_schema_field({
    'type': 'object',
    'properties': {
        'curies': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/relations/'
                }
            }
        },
        'self': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/categories/1'
                }
            }
        },
        'archives': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/signals/1/history/'
                }
            }
        },
        'sia:questionnaire': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/public/qa/questionnaires/'
                               '636aacb1-2813-423e-adbe-7ef84d4afc37',
                }
            }
        },
        'sia:icon': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/media/icons/1.png'
                }
            }
        },
    }
})
class CategoryLinksField(LinksField):
    def to_representation(self, value):
        request = self.context.get('request')
        result = OrderedDict([
            ('curies', {'name': 'sia', 'href': reverse('signal-namespace', request=request)}),
            ('self', {'href': category_public_url(value, request)}),
        ])

        if value.questionnaire:
            result.update({
                'sia:questionnaire': {
                    'href': reverse(
                        'questionnaires:public-questionnaire-detail',
                        kwargs={'uuid': value.questionnaire.uuid},
                        request=request,
                    )
                },
            })

        if value.has_icon():
            # Return the icon
            result.update({'sia:icon': {'href': request.build_absolute_uri(value.icon.url)}})
        elif value.is_child() and value.parent.has_icon():
            # Return the icon from the parent if no icon has been set on the child category
            result.update({'sia:icon': {'href': request.build_absolute_uri(value.parent.icon.url)}})

        return result


@extend_schema_field({
    'type': 'string',
    'format': 'uri',
    'example': 'https://api.example.com/signals/v1/public/terms/categories/1/sub_categories/2/'
})
class CategoryHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
    view_name = 'public-subcategory-detail'
    queryset = Category.objects.all().select_related('parent')
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

    def to_internal_value(self, data):
        return super().to_internal_value(data=data)


@extend_schema_field({
    'type': 'object',
    'properties': {
        'curies': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/relations/'
                }
            }
        },
        'self': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/categories/1'
                }
            }
        },
        'archives': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/signals/1/history/'
                }
            }
        },
        'sia:status-message-templates': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/status-messages/category/1'
                }
            }
        },
    }
})
class PrivateCategoryLinksField(LinksField):
    def _get_public_url(self, obj, request=None):
        return category_public_url(obj, request=request)

    def _get_status_message_templates_url(self, obj, request=None):
        if obj.is_child():
            viewname, kwargs = 'private-status-message-templates-child', {'slug': obj.parent.slug, 'sub_slug': obj.slug}
        else:
            viewname, kwargs = 'private-status-message-templates-parent', {'slug': obj.slug}
        return reverse(viewname, kwargs=kwargs, request=request)

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('curies', {'name': 'sia', 'href': reverse('signal-namespace', request=request)}),
            ('self', {
                'href': self.get_url(value, 'private-category-detail', request, None),
                'public': self._get_public_url(obj=value, request=request),
            }),
            ('archives', {'href': self.get_url(value, 'private-category-history', request, None)}),
            ('sia:status-message-templates', {
                'href': self._get_status_message_templates_url(obj=value, request=request)
            }),
        ])

        if value.is_child():
            result.update({'sia:parent': {
                'href': self.get_url(value.parent, 'private-category-detail', request, None),
                'public': self._get_public_url(obj=value.parent, request=request)
            }})

        if value.questionnaire:
            result.update({
                'sia:questionnaire': {
                    'href': reverse(
                        'questionnaires:public-questionnaire-detail',
                        kwargs={'uuid': value.questionnaire.uuid},
                        request=request,
                    ),
                }
            })

        if value.has_icon():
            # Return the icon
            result.update({'sia:icon': {'href': request.build_absolute_uri(value.icon.url)}})
        elif value.is_child() and value.parent.has_icon():
            # Return the icon from the parent if no icon has been set on the child category
            result.update({'sia:icon': {'href': request.build_absolute_uri(value.parent.icon.url)}})

        return result
