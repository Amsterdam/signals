# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import json

from django.forms.widgets import Textarea


class PrettyJSONWidget(Textarea):
    def format_value(self, value):
        try:
            value = json.dumps(json.loads(value), indent=4, sort_keys=True)
            row_lengths = [len(r) for r in value.split('\n')]
            self.attrs['rows'] = min(max(len(row_lengths) + 4, 10), 30)
            self.attrs['cols'] = min(max(max(row_lengths) + 4, 40), 120)
            return value
        except Exception:
            return super(PrettyJSONWidget, self).format_value(value)
