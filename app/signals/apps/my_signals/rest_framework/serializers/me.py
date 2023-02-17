# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from rest_framework import serializers


class MySignalsLoggedInReporterSerializer(serializers.Serializer):
    email = serializers.EmailField(read_only=True)
