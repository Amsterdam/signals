# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django import template

register = template.Library()


@register.filter
def is_a_list(value):
    return isinstance(value, (list, tuple))
