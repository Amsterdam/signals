# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam

# TODO: Find a better place for this file
from django.db.models import Func


class AsGeoJSON(Func):
    function = 'st_asgeojson'
    template = '%(function)s(%(expressions)s)::jsonb'
