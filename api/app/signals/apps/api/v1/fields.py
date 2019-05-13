"""
Signals API V1 custom serializer fields.
"""
from collections import OrderedDict

from rest_framework import serializers
from rest_framework.reverse import reverse

from signals.apps.signals.models import Attachment, Category, Signal


class ParentCategoryHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    lookup_field = 'slug'

    def to_representation(self, value):
        request = self.context.get('request')
        result = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request))),
            ('self', dict(href=self.get_url(value, 'category-detail', request, None))),
            ('sia:status-message-templates',
             dict(
                 href=self.get_url(value, 'status_message_templates_main_category', request, None)
             )),
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
            ('sia:status-message-templates',
             dict(href=self.get_url(value, 'status_message_templates', request, None))),
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
            ('curies', dict(name='sia', href=self.reverse("signal-namespace", request=request))),
            ('self', dict(href=self.get_url(value, "private-signals-detail", request, None))),
            ('archives', dict(href=self.get_url(value, "private-signals-history", request, None))),
            ('sia:attachments',
             dict(href=self.get_url(value, "private-signals-attachments", request, None))),
            ('sia:pdf', dict(href=self.get_url(value, "signal-pdf-download", request, None))),
        ])

        if value.is_child():
            result.update({
                'sia:parent':
                dict(href=self.get_url(value.parent, "private-signals-detail", request, None))
            })

        if value.is_parent():
            result.update({'sia:children': [
                dict(href=self.get_url(child, "private-signals-detail", request, None))
                for child in value.children.all()
            ]})

        return result


class PrivateSignalLinksField(serializers.HyperlinkedIdentityField):

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(href=self.get_url(value, "v1:private-signals-detail", request, None))),
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


class PublicSignalAttachmentLinksField(serializers.HyperlinkedIdentityField):
    lookup_field = 'signal_id'

    def to_representation(self, value: Attachment):
        request = self.context.get('request')

        result = OrderedDict([
            ('self',
             dict(href=self.get_url(value._signal, "public-signals-attachments", request, None))),
        ])

        return result


class PrivateSignalAttachmentLinksField(serializers.HyperlinkedIdentityField):
    def to_representation(self, value: Attachment):
        request = self.context.get('request')

        result = OrderedDict([
            ('self',
             dict(href=self.get_url(value._signal, "private-signals-attachments", request, None))),
        ])

        return result


class PrivateSignalSplitLinksField(serializers.HyperlinkedIdentityField):
    def to_representation(self, signal: Signal):
        request = self.context.get('request')

        result = OrderedDict([
            ('self',
             dict(href=self.get_url(signal, "v1:private-signals-split", request, None))),
        ])

        return result
