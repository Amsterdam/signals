# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.conf import settings


def settings_in_context(request):
    return {
        'FEATURE_FLAGS': settings.FEATURE_FLAGS,
        'ORGANIZATION_NAME': settings.ORGANIZATION_NAME,
    }
