# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import json

from rest_framework.renderers import BaseRenderer


class SerializedJsonRenderer(BaseRenderer):
    """
    This renderer is useful when the data source is already serialized JSON.

    It is used, for example, when serialized JSON is extracted from Postgres
    directly while bypassing the Django REST Framework renderers.
    """
    format = 'json'
    media_type = 'application/json'

    def render(self, data, media_type=None, renderer_context=None):
        if renderer_context and 'indent' in renderer_context:
            # This code path indents the JSON string for use in browsable API.
            return json.dumps(json.loads(data), indent=renderer_context['indent'])
        return data
