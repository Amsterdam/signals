from django import template
from django.conf import settings

from signals.apps.signals.utils.location import AddressFormatter

register = template.Library()


DEFAULT_ADDRESS_FORMAT = getattr(settings, 'ADDRESS_FORMAT', 'O hl, P W')


@register.filter
def format_address(location, format_str=DEFAULT_ADDRESS_FORMAT):
    return AddressFormatter(location.address).format(format_str=format_str)
