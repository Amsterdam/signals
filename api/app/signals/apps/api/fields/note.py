# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from collections import OrderedDict

from rest_framework import serializers


class NoteHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(
                href=self.get_url(value, "note-auth-detail", request, None))
             ),
        ])

        return result
