import uuid
from datetime import datetime

import pytz
from factory import DjangoModelFactory, RelatedFactory, post_generation
from factory.fuzzy import FuzzyAttribute, FuzzyDateTime, FuzzyText

from signals.apps.signals.models import Signal


class SignalFactory(DjangoModelFactory):
    class Meta:
        model = Signal

    signal_id = FuzzyAttribute(uuid.uuid4)
    text = FuzzyText(length=100)
    text_extra = FuzzyText(length=100)

    # Creating (reverse FK) related objects after this `Signal` is created.
    location = RelatedFactory('signals.apps.signals.factories.location.LocationFactory', '_signal')
    status = RelatedFactory('signals.apps.signals.factories.status.StatusFactory', '_signal')
    category_assignment = RelatedFactory(
        'signals.apps.signals.factories.category_assignment.CategoryAssignmentFactory',
        '_signal',
    )
    reporter = RelatedFactory('signals.apps.signals.factories.reporter.ReporterFactory', '_signal')
    priority = RelatedFactory('signals.apps.signals.factories.priority.PriorityFactory', '_signal')

    incident_date_start = FuzzyDateTime(datetime(2017, 11, 1, tzinfo=pytz.UTC), datetime(2018, 2, 1, tzinfo=pytz.UTC))
    incident_date_end = FuzzyDateTime(datetime(2018, 2, 2, tzinfo=pytz.UTC), datetime(2019, 2, 2, tzinfo=pytz.UTC))
    extra_properties = {}

    # SIG-884
    parent = None

    @post_generation
    def set_one_to_one_relations(self, create, extracted, **kwargs):
        """Set o2o relations on given `Signal` object."""
        self.location = self.locations.last()
        self.status = self.statuses.last()
        self.category_assignment = self.category_assignments.last()
        self.reporter = self.reporters.last()
        self.priority = self.priorities.last()

    @post_generation
    def set_default_type(self, create, extracted, **kwargs):
        """
        This will add the default Type to the signal for a factory created signal
        """
        if create:
            from . import TypeFactory
            TypeFactory(_signal=self)  # By default the type is set to "SIG (SIGNAL)"


class SignalFactoryWithImage(SignalFactory):
    attachment = RelatedFactory('signals.apps.signals.factories.attachment.ImageAttachmentFactory', '_signal')


class SignalFactoryValidLocation(SignalFactory):
    location = RelatedFactory('signals.apps.signals.factories.location.ValidLocationFactory', '_signal')
