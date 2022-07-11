# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from collections import OrderedDict

from rest_framework import serializers

from signals.apps.signals.models import Signal


class PrivateSignalLinksFieldWithArchives(serializers.HyperlinkedIdentityField):
    def to_representation(self, value: Signal) -> OrderedDict:
        request = self.context.get('request')

        result = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse("signal-namespace", request=request))),
            ('self', dict(href=self.get_url(value, "private-signals-detail", request, None))),
            ('archives', dict(href=self.get_url(value, "private-signals-history", request, None))),
            ('sia:attachments', dict(href=self.reverse("private-signals-attachments-list",
                                                       kwargs={'parent_lookup__signal__pk': value.pk},
                                                       request=request))),
            ('sia:pdf', dict(href=self.get_url(value, "private-signals-pdf-download", request, None))),
            ('sia:context', dict(href=self.get_url(value, 'private-signal-context', request, None))),
        ])

        if value.is_child:
            result.update({
                'sia:parent':
                dict(href=self.get_url(value.parent, "private-signals-detail", request, None))
            })

        if value.is_parent:
            result.update({'sia:children': [
                dict(href=self.get_url(child, "private-signals-detail", request, None))
                for child in value.children.all()
            ]})

        return result


class PrivateSignalLinksField(serializers.HyperlinkedIdentityField):

    def to_representation(self, value: Signal) -> OrderedDict:
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(href=self.get_url(value, "private-signals-detail", request, None))),
        ])

        return result


class PrivateSignalWithContextLinksField(serializers.HyperlinkedIdentityField):

    def to_representation(self, value: Signal) -> OrderedDict:
        request = self.context.get('request')

        result = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request))),
            ('self', dict(href=self.get_url(value, 'private-signal-context', request, None))),
            ('sia:context-reporter-detail', dict(href=self.get_url(
                value, 'private-signal-context-reporter', request, None))),
            ('sia:context-geography-detail', dict(href=self.get_url(
                value, 'private-signal-context-near-geography', request, None))),
        ])

        return result


class PublicSignalLinksField(serializers.HyperlinkedIdentityField):
    lookup_field = 'signal_id'

    def to_representation(self, value: Signal) -> OrderedDict:
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(href=self.get_url(value, "public-signals-detail", request, None))),
        ])

        return result
