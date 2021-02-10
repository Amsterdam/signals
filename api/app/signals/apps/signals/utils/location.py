import re
from typing import Optional

from django.conf import settings
from django.contrib.gis.db.models import PointField
from django.db.models import Q

from signals.apps.signals.models import Area


def _get_area(geometry: PointField, area_type: Optional[str] = None) -> Optional[Area]:
    """
    Returns the first Area found based on the given
    Retrieves the Area based on the geometry and area type, returns None is the Area is not found

    :param geometry:
    :param area_type:
    :return: Area or None
    """
    query = Q(geometry__contains=geometry)
    if area_type:
        query &= Q(_type__code=area_type)

    areas = Area.objects.filter(query)
    return areas.first() if areas.exists() else None


def _get_stadsdeel_code(geometry: PointField, default: Optional[str] = None) -> Optional[str]:
    """
    Translate the Area "code" to the STADSDELEN "code", returns None if there is no translation

    :param geometry:
    :param default:
    :return: str or None
    """
    if not settings.FEATURE_FLAGS.get('API_DETERMINE_STADSDEEL_ENABLED', False):
        return default

    from signals.apps.signals.models.location import AREA_STADSDEEL_TRANSLATION

    area_type = getattr(settings, 'API_DETERMINE_STADSDEEL_ENABLED_AREA_TYPE', 'sia-stadsdeel')
    area = _get_area(geometry=geometry, area_type=area_type)
    code = AREA_STADSDEEL_TRANSLATION.get(area.code.lower(), None) if area else None
    return code or default


class AddressFormatter:
    """
    Based on the format classes found in django.utils.dateformat
    """
    re_formatchars = re.compile(r'(?<!\\)([OhltTpPW])')
    re_escaped = re.compile(r'\\(.)')

    def __init__(self, address):
        self.address = address

    def O(self):  # noqa E743
        """
        Openbare ruimte
        """
        return self.address['openbare_ruimte'] if self.address and 'openbare_ruimte' in self.address else ''

    def h(self):
        """
        Huisnummer
        """
        return self.address['huisnummer'] if self.address and 'huisnummer' in self.address else ''

    def l(self):  # noqa E743
        """
        Huisletter
        """
        return self.address['huisletter'] if self.address and 'huisletter' in self.address else ''

    def t(self):
        """
        Huisnummer toevoeging  without a hyphen
        """
        return self.address['huisnummer_toevoeging'] if self.address and 'huisnummer_toevoeging' in self.address else ''

    def T(self):  # noqa E743
        """
        Huisnummer toevoeging with a hyphen
        """
        if self.address and 'huisnummer_toevoeging' in self.address \
                and len(self.address['huisnummer_toevoeging'].strip()) > 0:
            return f'-{self.address["huisnummer_toevoeging"]}'
        else:
            return ''

    def p(self):
        """
        Postcode without a space between the digits and the characters
        """
        # Returns a postal code in the following format "1234AA"
        return self.address['postcode'] if self.address and 'postcode' in self.address else ''

    def P(self):  # noqa E743
        """
        Postcode with a space between the digits and the characters
        """
        # Returns a postal code in the following format "1234 AA"
        return str(re.sub('(^[0-9]+)', r' \1 ', self.address['postcode'])).strip() \
            if self.address and 'postcode' in self.address else ''

    def W(self):  # noqa E743
        """
        Woonplaats
        """
        return self.address['woonplaats'] if self.address and 'woonplaats' in self.address else ''

    def format(self, format_str):
        formatted_string = []
        for i, format_char in enumerate(self.re_formatchars.split(str(format_str))):
            if i % 2:
                formatted_string.append(str(getattr(self, format_char)()))
            elif format_char:
                formatted_string.append(self.re_escaped.sub(r'\1', format_char))
        return ''.join(formatted_string)
