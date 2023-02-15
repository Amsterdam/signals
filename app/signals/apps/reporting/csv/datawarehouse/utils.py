# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.db.models import Func


class ToJsonB(Func):
    # TODO: Find a better place for this code
    function = 'to_jsonb'
