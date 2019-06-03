import copy

from django.contrib.gis.db import models
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.postgres.fields import JSONField

from signals.apps.signals.models.buurt import Buurt
from signals.apps.signals.models.mixins import CreatedUpdatedModel

STADSDEEL_CENTRUM = 'A'
STADSDEEL_WESTPOORT = 'B'
STADSDEEL_WEST = 'E'
STADSDEEL_OOST = 'M'
STADSDEEL_NOORD = 'N'
STADSDEEL_ZUIDOOST = 'T'
STADSDEEL_ZUID = 'K'
STADSDEEL_NIEUWWEST = 'F'
STADSDELEN = (
    (STADSDEEL_CENTRUM, 'Centrum'),
    (STADSDEEL_WESTPOORT, 'Westpoort'),
    (STADSDEEL_WEST, 'West'),
    (STADSDEEL_OOST, 'Oost'),
    (STADSDEEL_NOORD, 'Noord'),
    (STADSDEEL_ZUIDOOST, 'Zuidoost'),
    (STADSDEEL_ZUID, 'Zuid'),
    (STADSDEEL_NIEUWWEST, 'Nieuw-West'),
)

_ADDRESS_FIELD_PREFIXES = (
    ('openbare_ruimte', ''),
    ('huisnummer', ' '),
    ('huisletter', ''),
    ('huisnummer_toevoeging', '-'),
    ('postcode', ' '),
    ('woonplaats', ' ')
)


def get_buurt_code_choices():
    return Buurt.objects.values_list('vollcode', 'naam')


def get_address_text(location, field_prefixes=_ADDRESS_FIELD_PREFIXES):
    """Generate address text, shortened if needed."""

    address_text = ''
    if location.address and isinstance(location.address, dict):
        for field, prefix in field_prefixes:
            if field in location.address and location.address[field]:
                address_text += prefix + str(location.address[field])

    return address_text


class Location(CreatedUpdatedModel):
    """All location related information."""

    _signal = models.ForeignKey(
        "signals.Signal", related_name="locations",
        null=False, on_delete=models.CASCADE
    )

    geometrie = models.PointField(name="geometrie")
    stadsdeel = models.CharField(
        null=True, max_length=1, choices=STADSDELEN)
    # we do NOT use foreign key, since we update
    # buurten as external data in a seperate process
    buurt_code = models.CharField(null=True, max_length=4)
    address = JSONField(null=True)
    address_text = models.CharField(null=True, max_length=256, editable=False)
    created_by = models.EmailField(null=True, blank=True)

    extra_properties = JSONField(null=True)
    bag_validated = models.BooleanField(default=False)

    @property
    def short_address_text(self):
        # no postal code, no municipality
        field_prefixes = copy.deepcopy(_ADDRESS_FIELD_PREFIXES)
        field_prefixes = field_prefixes[:-2]

        return get_address_text(self, field_prefixes)

    def set_address_text(self):
        self.address_text = get_address_text(self)

    def save(self, *args, **kwargs):
        # Set address_text
        self.set_address_text()
        super().save(*args, **kwargs)

    def get_rd_coordinates(self):
        to_transform = copy.deepcopy(self.geometrie)
        to_transform.transform(
            CoordTransform(
                SpatialReference(4326),  # WGS84
                SpatialReference(28992)  # RD
            )
        )
        return to_transform
