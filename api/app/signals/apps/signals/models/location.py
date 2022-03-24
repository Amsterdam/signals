# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import copy

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models
from django.contrib.gis.gdal import CoordTransform, SpatialReference

from signals.apps.signals.models.mixins import CreatedUpdatedModel
from signals.apps.signals.utils.location import AddressFormatter

STADSDEEL_CENTRUM = 'A'
STADSDEEL_WESTPOORT = 'B'
STADSDEEL_WEST = 'E'
STADSDEEL_OOST = 'M'
STADSDEEL_NOORD = 'N'
STADSDEEL_ZUIDOOST = 'T'
STADSDEEL_ZUID = 'K'
STADSDEEL_NIEUWWEST = 'F'
STADSDEEL_AMSTERDAMSE_BOS = 'H'
STADSDEEL_WEESP = 'W'
STADSDELEN = (
    (STADSDEEL_CENTRUM, 'Centrum'),
    (STADSDEEL_WESTPOORT, 'Westpoort'),
    (STADSDEEL_WEST, 'West'),
    (STADSDEEL_OOST, 'Oost'),
    (STADSDEEL_NOORD, 'Noord'),
    (STADSDEEL_ZUIDOOST, 'Zuidoost'),
    (STADSDEEL_ZUID, 'Zuid'),
    (STADSDEEL_NIEUWWEST, 'Nieuw-West'),
    (STADSDEEL_AMSTERDAMSE_BOS, 'Het Amsterdamse Bos'),
    (STADSDEEL_WEESP, 'Weesp'),
)

AREA_STADSDEEL_TRANSLATION = {
    'het-amsterdamse-bos': STADSDEEL_AMSTERDAMSE_BOS,
    'zuidoost': STADSDEEL_ZUIDOOST,
    'centrum': STADSDEEL_CENTRUM,
    'noord': STADSDEEL_NOORD,
    'westpoort': STADSDEEL_WESTPOORT,
    'west': STADSDEEL_WEST,
    'nieuw-west': STADSDEEL_NIEUWWEST,
    'oost': STADSDEEL_OOST,
    'zuid': STADSDEEL_ZUID,
    'stadsdeel-zuid': STADSDEEL_ZUID,
    'weesp': STADSDEEL_WEESP,
}


class Location(CreatedUpdatedModel):
    """All location related information."""

    _signal = models.ForeignKey(
        'signals.Signal', related_name='locations',
        null=False, on_delete=models.CASCADE
    )

    geometrie = models.PointField(name='geometrie')
    stadsdeel = models.CharField(null=True, max_length=1, choices=STADSDELEN)
    area_type_code = models.CharField(null=True, max_length=256)
    area_code = models.CharField(null=True, max_length=256)
    area_name = models.CharField(null=True, max_length=256)  # used for sorting BE-166

    # we do NOT use foreign key, since we update
    # buurten as external data in a seperate process
    buurt_code = models.CharField(null=True, max_length=4)
    address = models.JSONField(null=True)
    address_text = models.CharField(null=True, max_length=256, editable=False)
    created_by = models.EmailField(null=True, blank=True)

    extra_properties = models.JSONField(null=True)
    bag_validated = models.BooleanField(default=False)

    history_log = GenericRelation('history.Log', object_id_field='object_pk')

    @property
    def short_address_text(self):
        # openbare_ruimte huisnummerhuiletter-huisnummer_toevoeging
        return AddressFormatter(address=self.address).format('O hlT') if self.address else ''

    def save(self, *args, **kwargs):
        # Set address_text
        self.address_text = AddressFormatter(address=self.address).format('O hlT p W') if self.address else ''
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


def _get_description_of_update_location(location_id):
    """Get descriptive text for location update history entries."""
    location = Location.objects.get(id=location_id)

    # Craft a message for UI
    desc = f'Stadsdeel: {location.get_stadsdeel_display()}' if location.stadsdeel else ''

    # Deal with address text or coordinates
    if location.address and isinstance(location.address, dict):
        # openbare_ruimte huisnummerhuisletter-huisummer_toevoeging woonplaats
        address_formatter = AddressFormatter(address=location.address)
        desc = f'{desc}\n{address_formatter.format("O hlT")}\n{address_formatter.format("W")}'
    else:
        desc = f'{desc}Locatie is gepind op de kaart\n{location.geometrie[0]}, {location.geometrie[1]}'

    return desc
