from typing import Optional

from django.conf import settings
from django.contrib.gis.db.models import PointField
from django.db.models import Q

from signals.apps.signals.models import Area
from signals.apps.signals.models.location import AREA_STADSDEEL_TRANSLATION


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

    area_type = getattr(settings, 'API_DETERMINE_STADSDEEL_ENABLED_AREA_TYPE', 'sia-stadsdeel')
    area = _get_area(geometry=geometry, area_type=area_type)
    code = AREA_STADSDEEL_TRANSLATION.get(area.code.lower(), None) if area else None
    return code or default
