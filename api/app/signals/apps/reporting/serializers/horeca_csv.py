# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from rest_framework import serializers

from signals.apps.reporting.models import HorecaCSVExport


class HorecaCSVExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorecaCSVExport
        fields = (
            'created_at',
            'created_by',
            'isoyear',
            'isoweek',
            'uploaded_file',
        )

        read_only = (
            'created_at',
            'created_by',
            'isoyear',
            'isoweek',
            'uploaded_file',
        )
