import copy
import random
import string
import uuid
from datetime import datetime

import factory
import pytz
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.utils.text import slugify
from factory import fuzzy

from signals.apps.signals.models import (
    STADSDELEN,
    Area,
    AreaType,
    Attachment,
    Category,
    CategoryAssignment,
    Department,
    Location,
    Note,
    Priority,
    Question,
    Reporter,
    Signal,
    Status,
    StatusMessageTemplate,
    StoredSignalFilter,
    Type
)
from signals.apps.signals.workflow import GEMELD, STATUS_CHOICES_API
from tests.apps.signals.valid_locations import VALID_LOCATIONS

# Amsterdam.
BBOX = [4.58565, 52.03560, 5.31360, 52.48769]


def get_puntje():

    lon = fuzzy.FuzzyFloat(BBOX[0], BBOX[2]).fuzz()
    lat = fuzzy.FuzzyFloat(BBOX[1], BBOX[3]).fuzz()
    return Point(float(lon), float(lat))


def get_random_bbox(bbox=BBOX, n_lon_subdiv=10, n_lat_subdiv=10):
    # Assumes we are away from the antimeridian (i.e. max_lat > min_lat).
    min_lon, min_lat, max_lon, max_lat = bbox
    extent_lon = max_lon - min_lon
    extent_lat = max_lat - min_lat

    ilon = random.randrange(n_lon_subdiv)
    ilat = random.randrange(n_lat_subdiv)

    return Polygon.from_bbox((
        min_lon + (extent_lon / n_lon_subdiv) * ilon,
        min_lat + (extent_lat / n_lat_subdiv) * ilat,
        min_lon + (extent_lon / n_lon_subdiv) * (ilon + 1),
        min_lat + (extent_lat / n_lat_subdiv) * (ilat + 1),
    ))


class SignalFactory(factory.DjangoModelFactory):

    class Meta:
        model = Signal

    signal_id = fuzzy.FuzzyAttribute(uuid.uuid4)
    text = fuzzy.FuzzyText(length=100)
    text_extra = fuzzy.FuzzyText(length=100)

    # Creating (reverse FK) related objects after this `Signal` is created.
    location = factory.RelatedFactory('tests.apps.signals.factories.LocationFactory', '_signal')
    status = factory.RelatedFactory('tests.apps.signals.factories.StatusFactory', '_signal')
    category_assignment = factory.RelatedFactory(
        'tests.apps.signals.factories.CategoryAssignmentFactory', '_signal')
    reporter = factory.RelatedFactory('tests.apps.signals.factories.ReporterFactory', '_signal')
    priority = factory.RelatedFactory('tests.apps.signals.factories.PriorityFactory', '_signal')

    incident_date_start = fuzzy.FuzzyDateTime(
        datetime(2017, 11, 1, tzinfo=pytz.UTC),
        datetime(2018, 2, 1, tzinfo=pytz.UTC),
    )
    incident_date_end = fuzzy.FuzzyDateTime(
        datetime(2018, 2, 2, tzinfo=pytz.UTC),
        datetime(2019, 2, 2, tzinfo=pytz.UTC)
    )
    extra_properties = {}

    # SIG-884
    parent = None

    @factory.post_generation
    def set_one_to_one_relations(self, create, extracted, **kwargs):
        """Set o2o relations on given `Signal` object."""
        self.location = self.locations.last()
        self.status = self.statuses.last()
        self.category_assignment = self.category_assignments.last()
        self.reporter = self.reporters.last()
        self.priority = self.priorities.last()

    @factory.post_generation
    def set_default_type(self, create, extracted, **kwargs):
        """
        This will add the default Type to the signal for a factory created signal
        """
        if create:
            TypeFactory(_signal=self)  # By default the type is set to "SIG (SIGNAL)"


class SignalFactoryWithImage(SignalFactory):

    attachment = factory.RelatedFactory('tests.apps.signals.factories.ImageAttachmentFactory',
                                        '_signal')


class ImageAttachmentFactory(factory.DjangoModelFactory):

    class Meta:
        model = Attachment

    _signal = factory.SubFactory('tests.apps.signals.factories.SignalFactory')
    created_by = factory.Sequence(lambda n: 'veelmelder{}@example.com'.format(n))
    file = factory.django.ImageField()  # In reality it's a FileField, but we want to force an image
    is_image = True

    @factory.post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
        self.is_image = True
        self.save()


class SignalFactoryValidLocation(SignalFactory):
    location = factory.RelatedFactory(
        'tests.apps.signals.factories.ValidLocationFactory', '_signal')


class LocationFactory(factory.DjangoModelFactory):

    class Meta:
        model = Location

    _signal = factory.SubFactory('tests.apps.signals.factories.SignalFactory', location=None)

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


class ReporterFactory(factory.DjangoModelFactory):

    class Meta:
        model = Reporter

    _signal = factory.SubFactory('tests.apps.signals.factories.SignalFactory', reporter=None)

    email = factory.Sequence(lambda n: 'veelmelder{}@example.com'.format(n))
    email_anonymized = False

    phone = fuzzy.FuzzyText(length=10, chars=string.digits)
    phone_anonymized = False

    @factory.post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal


class CategoryAssignmentFactory(factory.DjangoModelFactory):

    class Meta:
        model = CategoryAssignment

    _signal = factory.SubFactory('tests.apps.signals.factories.SignalFactory',
                                 category_assignment=None)
    category = factory.SubFactory('tests.apps.signals.factories.CategoryFactory')

    @factory.post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal


class StatusFactory(factory.DjangoModelFactory):

    class Meta:
        model = Status

    _signal = factory.SubFactory('tests.apps.signals.factories.SignalFactory', status=None)

    text = fuzzy.FuzzyText(length=400)
    user = factory.Sequence(lambda n: 'veelmelder{}@example.com'.format(n))
    state = GEMELD  # Initial state is always 'm'
    extern = fuzzy.FuzzyChoice((True, False))

    @factory.post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal


class PriorityFactory(factory.DjangoModelFactory):

    class Meta:
        model = Priority

    _signal = factory.SubFactory('tests.apps.signals.factories.SignalFactory', priority=None)

    @factory.post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal


#
# Category declarations
#


class ParentCategoryFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Parent category {}'.format(n))
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    handling = fuzzy.FuzzyChoice([c[0] for c in Category.HANDLING_CHOICES])
    handling_message = 'Test handling message (parent category)'
    is_active = True

    class Meta:
        model = Category
        django_get_or_create = ('slug', )

    @factory.post_generation
    def questions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for question in extracted:
                self.questions.add(question)


class CategoryFactory(factory.DjangoModelFactory):
    parent = factory.SubFactory('tests.apps.signals.factories.ParentCategoryFactory')
    name = factory.Sequence(lambda n: 'Category {}'.format(n))
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    handling = fuzzy.FuzzyChoice([c[0] for c in Category.HANDLING_CHOICES])
    handling_message = 'Test handling message (child category)'
    is_active = True

    class Meta:
        model = Category
        django_get_or_create = ('parent', 'slug', )

    @factory.post_generation
    def departments(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for department in extracted:
                self.departments.add(
                    department,
                    through_defaults={
                        'is_responsible': True,
                        'can_view': True
                    }
                )

    @factory.post_generation
    def questions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for question in extracted:
                self.questions.add(question)


class DepartmentFactory(factory.DjangoModelFactory):
    code = fuzzy.FuzzyText(length=3)
    name = fuzzy.FuzzyText(length=10)
    is_intern = fuzzy.FuzzyChoice(choices=[True, False])

    class Meta:
        model = Department


class QuestionFactory(factory.DjangoModelFactory):
    key = fuzzy.FuzzyText(length=3)
    field_type = fuzzy.FuzzyChoice(choices=list(dict(Question.FIELD_TYPE_CHOICES).keys()))
    meta = '{ "dummy" : "test" }'
    required = fuzzy.FuzzyChoice(choices=[True, False])

    class Meta:
        model = Question


class NoteFactory(factory.DjangoModelFactory):
    text = fuzzy.FuzzyText(length=100)
    created_by = factory.Sequence(lambda n: 'ambtenaar{}@example.com'.format(n))
    _signal = factory.SubFactory('tests.apps.signals.factories.SignalFactory')

    class Meta:
        model = Note


class StatusMessageTemplateFactory(factory.DjangoModelFactory):
    title = fuzzy.FuzzyText(length=100)
    text = fuzzy.FuzzyText(length=100)
    order = 0
    category = factory.SubFactory('tests.apps.signals.factories.CategoryFactory')
    state = factory.LazyAttribute(lambda o: random.choice(STATUS_CHOICES_API)[0])

    class Meta:
        model = StatusMessageTemplate


class StoredSignalFilterFactory(factory.DjangoModelFactory):
    name = fuzzy.FuzzyText(length=100)

    class Meta:
        model = StoredSignalFilter


class TypeFactory(factory.DjangoModelFactory):
    _signal = factory.SubFactory('tests.apps.signals.factories.SignalFactory')
    name = Type.SIGNAL  # Default type is a "Signal" (Melding in Dutch)

    class Meta:
        model = Type


class AreaTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = AreaType

    name = factory.Sequence(lambda n: f'Gebied type {n}')
    code = factory.Sequence(lambda n: f'gebied-type-code-{n}')
    description = factory.Sequence(lambda n: f'Omschrijving bij gebied type {n}')


class AreaFactory(factory.DjangoModelFactory):
    class Meta:
        model = Area

    name = factory.Sequence(lambda n: f'Gebied type {n}')
    code = factory.Sequence(lambda n: f'gebied-type-code-{n}')
    _type = factory.SubFactory(AreaTypeFactory)
    geometry = MultiPolygon([get_random_bbox()])
