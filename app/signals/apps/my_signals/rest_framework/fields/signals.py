# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from collections import OrderedDict

from rest_framework.relations import HyperlinkedIdentityField

from signals.apps.signals.models import Signal


class MySignalListLinksField(HyperlinkedIdentityField):
    lookup_field = 'uuid'

    def to_representation(self, value: Signal) -> OrderedDict:
        request = self.context.get('request')
        _format = self.context.get('format')

        return OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request, format=_format))),
            ('self', dict(href=self.get_url(value, 'my_signals:my-signals-detail', request, _format))),
        ])


class MySignalDetailLinksField(HyperlinkedIdentityField):
    lookup_field = 'uuid'

    def to_representation(self, value: Signal) -> OrderedDict:
        request = self.context.get('request')
        _format = self.context.get('format')

        representation = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request, format=_format))),
            ('self', dict(href=self.get_url(value, 'my_signals:my-signals-detail', request, _format))),
            ('archives', dict(href=self.get_url(value, 'my_signals:my-signals-history', request, _format))),
        ])

        attachment_qs = value.attachments.filter(created_by__isnull=True, is_image=True)
        if attachment_qs.exists():
            # A list URI's of all the attachments
            representation.update({
                ('sia:attachments', (
                    {
                        'href': request.build_absolute_uri(attachment.file.url),
                        'created_by': attachment.created_by,
                        'created_at': attachment.created_at,
                    }
                    for attachment in attachment_qs.all().order_by('-created_at')
                )),
            })

        return representation
