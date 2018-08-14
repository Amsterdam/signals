import pytz
import string
import uuid
import random
from datetime import datetime

import factory
from django.contrib.gis.geos import Point
from django.db.models.signals import pre_save, post_save
from factory import fuzzy

from signals.models import Signal
from signals.models import Location
from signals.models import Reporter
from signals.models import Category
from signals.models import Status
from signals.models import GEMELD

# Amsterdam.
BBOX = [52.03560, 4.58565, 52.48769, 5.31360]


def get_puntje():

    lat = fuzzy.FuzzyFloat(BBOX[0], BBOX[2]).fuzz()
    lon = fuzzy.FuzzyFloat(BBOX[1], BBOX[3]).fuzz()
    return Point(float(lat), float(lon))


@factory.django.mute_signals(pre_save, post_save)
class SignalFactory(factory.DjangoModelFactory):

    class Meta:
        model = Signal

    # This is needed to make the back reference `_signal` on o2o related
    # objects possible.
    id = factory.Sequence(lambda n: n)

    signal_id = fuzzy.FuzzyAttribute(uuid.uuid4)
    text = fuzzy.FuzzyText(length=100)
    text_extra = fuzzy.FuzzyText(length=100)

    location = factory.SubFactory('signals.tests.factories.LocationFactory',
                                  _signal_id=factory.SelfAttribute('..id'))
    status = factory.SubFactory('signals.tests.factories.StatusFactory',
                                _signal_id=factory.SelfAttribute('..id'))
    category = factory.SubFactory('signals.tests.factories.CategoryFactory',
                                  _signal_id=factory.SelfAttribute('..id'))
    reporter = factory.SubFactory('signals.tests.factories.ReporterFactory',
                                  _signal_id=factory.SelfAttribute('..id'))

    incident_date_start = fuzzy.FuzzyDateTime(
        datetime(2017, 11, 1, tzinfo=pytz.UTC),
        datetime(2018, 2, 1, tzinfo=pytz.UTC),
    )
    incident_date_end = fuzzy.FuzzyDateTime(
        datetime(2018, 2, 2, tzinfo=pytz.UTC),
        datetime(2019, 2, 2, tzinfo=pytz.UTC)
    )
    extra_properties = {}


class LocationFactory(factory.DjangoModelFactory):

    class Meta:
        model = Location

    buurt_code = fuzzy.FuzzyText(length=4)
    stadsdeel = fuzzy.FuzzyText(length=1)
    geometrie = get_puntje()
    address = {'straat': 'Sesamstraat',
               'huisnummer': 666,
               'postcode': '1011AA',
               'openbare_ruimte': 'Ergens'}


class ReporterFactory(factory.DjangoModelFactory):

    class Meta:
        model = Reporter

    phone = fuzzy.FuzzyText(length=10, chars=string.digits)
    email = 'john%d@example.org' % (int(random.random() * 100))


class CategoryFactory(factory.DjangoModelFactory):

    class Meta:
        model = Category

    main = fuzzy.FuzzyText(length=10)
    sub = fuzzy.FuzzyText(length=10)


class StatusFactory(factory.DjangoModelFactory):

    class Meta:
        model = Status

    user = 'kees%s@amsterdam.nl' % (int(random.random() * 100))
    text = fuzzy.FuzzyText(length=400)

    state = GEMELD  # Initial state is always 'm'
    extern = fuzzy.FuzzyChoice((True, False))
