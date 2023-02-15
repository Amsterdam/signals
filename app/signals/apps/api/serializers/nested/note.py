# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.signals.models import Note


class _NestedNoteModelSerializer(SIAModelSerializer):
    class Meta:
        model = Note
        fields = (
            'text',
            'created_by',
        )
        read_only_fields = (
            'created_by',
        )
