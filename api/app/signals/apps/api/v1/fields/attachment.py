# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from collections import OrderedDict

from rest_framework import serializers
from rest_framework.request import Request

from signals.apps.signals.models import Attachment


class PublicSignalAttachmentLinksField(serializers.HyperlinkedIdentityField):
    lookup_field = 'uuid'

    def to_representation(self, value: Attachment):
        request = self.context.get('request')

        result = OrderedDict([
            ('self',
             dict(href=self.get_url(value._signal, "public-signals-attachments", request, None))),
        ])

        return result


class PrivateSignalAttachmentLinksField(serializers.HyperlinkedIdentityField):
    def to_representation(self, value: Attachment) -> OrderedDict:
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(href=self.reverse("private-signals-attachments-detail",
                                            kwargs={'parent_lookup__signal__pk': value._signal_id, 'pk': value.pk},
                                            request=request) if value.pk else None)),
        ])

        return result


class PrivateSignalAttachmentRelatedField(serializers.HyperlinkedRelatedField):
    def get_url(self, obj: Attachment, view_name: str, request: Request, format: str) -> str:
        return self.reverse("private-signals-attachments-detail",
                            kwargs={'parent_lookup__signal__pk': obj._signal_id, 'pk': obj.pk},
                            request=request)
