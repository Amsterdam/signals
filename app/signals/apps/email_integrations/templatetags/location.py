# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django import template
from django.conf import settings

from signals.apps.signals.models import Location
from signals.apps.signals.utils.location import AddressFormatter

register = template.Library()


DEFAULT_ADDRESS_FORMAT = getattr(settings, 'ADDRESS_FORMAT', 'O hl, P W')


@register.filter
def format_address(obj, format_str=DEFAULT_ADDRESS_FORMAT):
    if isinstance(obj, Location) and obj.address:
        # Deprecated way to format the address when getting a Location object.
        # Use in template {{ location|format_address:"O hlT, P W" }}
        #
        # This should be removed when all templates are using {{ address|format_address:"O hlT, P W" }}
        return AddressFormatter(obj.address).format(format_str=format_str)
    else:
        # Will format the address.
        # Use in template {{ address|format_address:"O hlT, P W" }}
        return AddressFormatter(obj).format(format_str=format_str)
