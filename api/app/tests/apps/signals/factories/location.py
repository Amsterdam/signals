import copy
import random

import factory
from django.contrib.gis.geos import Point
from factory import fuzzy

from signals.apps.signals.models import STADSDELEN, Location
from tests.apps.signals.valid_locations import VALID_LOCATIONS

# Amsterdam.
BBOX = [4.58565, 52.03560, 5.31360, 52.48769]


def get_puntje():
    lon = fuzzy.FuzzyFloat(BBOX[0], BBOX[2]).fuzz()
    lat = fuzzy.FuzzyFloat(BBOX[1], BBOX[3]).fuzz()
    return Point(float(lon), float(lat))


class LocationFactory(factory.DjangoModelFactory):

    class Meta:
        model = Location

    _signal = factory.SubFactory('tests.apps.signals.factories.signal.signal.SignalFactory', location=None)

    buurt_code = fuzzy.FuzzyText(length=4)
    stadsdeel = fuzzy.FuzzyChoice(choices=(s[0] for s in STADSDELEN))
    geometrie = get_puntje()
    address = {'straat': 'Sesamstraat',
               'huisnummer': 666,
               'postcode': '1011AA',
               'openbare_ruimte': 'Ergens'}

    @factory.post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal


class ValidLocationFactory(LocationFactory):
    @factory.post_generation
    def set_valid_location(self, create, extracted, **kwargs):
        valid_location = copy.copy(random.choice(VALID_LOCATIONS))

        longitude = valid_location.pop('lon')
        lattitude = valid_location.pop('lat')
        self.geometrie = Point(longitude, lattitude)
        self.buurt_code = valid_location.pop('buurt_code')
        self.stadsdeel = valid_location.pop('stadsdeel')
        self.address = valid_location
