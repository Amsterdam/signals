# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.db.models import Aggregate, JSONField


class JSONAgg(Aggregate):
    template = '%(function)s(%(distinct)s%(expressions)s)::jsonb'
    name = 'FeatureCollection'
    function = 'json_agg'
    output_field = JSONField()
