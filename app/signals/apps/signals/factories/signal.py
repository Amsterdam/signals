# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
import uuid
from datetime import timedelta
from typing import Any

from django.utils import timezone
from factory import LazyAttribute, LazyFunction, RelatedFactory, post_generation
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyAttribute, FuzzyChoice, FuzzyDateTime
from faker import Faker

from signals.apps.signals.models import Signal

fake = Faker()


def _incident_date_end(incident_date_start):
    """
    - Randomly decide if a Signal incident end date must be set
    - If decided to set the incident end date check if we can create a date between incident date start and now
    """
    if FuzzyChoice([True, False]).fuzz():
        now = timezone.now()
        if incident_date_start < now - timedelta(hours=1):
            return FuzzyDateTime(incident_date_start, now).fuzz()
    return None


class SignalFactory(DjangoModelFactory):
    class Meta:
        model = Signal

    uuid = FuzzyAttribute(uuid.uuid4)
    text = LazyFunction(fake.paragraph)
    text_extra = LazyFunction(fake.paragraph)

    # Creating (reverse FK) related objects after this `Signal` is created.
    location: RelatedFactory = RelatedFactory('signals.apps.signals.factories.location.LocationFactory', '_signal')
    status: RelatedFactory = RelatedFactory('signals.apps.signals.factories.status.StatusFactory', '_signal')
    category_assignment: RelatedFactory = RelatedFactory(
        'signals.apps.signals.factories.category_assignment.CategoryAssignmentFactory',
        '_signal',
    )
    reporter: RelatedFactory = RelatedFactory('signals.apps.signals.factories.reporter.ReporterFactory', '_signal')
    priority: RelatedFactory = RelatedFactory('signals.apps.signals.factories.priority.PriorityFactory', '_signal')
    type_assignment: RelatedFactory = RelatedFactory('signals.apps.signals.factories.type.TypeFactory', '_signal')

    incident_date_start = FuzzyDateTime(timezone.now() - timedelta(days=100), timezone.now())
    incident_date_end: LazyAttribute = LazyAttribute(lambda o: _incident_date_end(o.incident_date_start))
    extra_properties: dict[str, Any] = {}

    # SIG-884
    parent = None
    user_assignment: RelatedFactory = RelatedFactory(
        'signals.apps.signals.factories.signal_user.SignalUserFactory', '_signal', user=None
    ) # noqa

    @post_generation
    def set_one_to_one_relations(self, create, extracted, **kwargs):
        """Set o2o relations on given `Signal` object."""
        self.location = self.locations.last()
        self.status = self.statuses.last()
        self.category_assignment = self.category_assignments.last()
        self.reporter = self.reporters.last()
        self.priority = self.priorities.last()
        self.type_assignment = self.types.last()

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        """Save again the instance if creating and at least one hook ran.

        Deprecated: https://factoryboy.readthedocs.io/en/stable/changelog.html
        To fix this warning, we override _after_postgeneration to save() the instance.
        """
        if create:
            # Some post-generation hooks ran, and may have modified us.
            instance.save()


class SignalFactoryWithImage(SignalFactory):
    attachment: RelatedFactory = RelatedFactory(
        'signals.apps.signals.factories.attachment.ImageAttachmentFactory', '_signal'
    )


class SignalFactoryValidLocation(SignalFactory):
    location: RelatedFactory = RelatedFactory(
        'signals.apps.signals.factories.location.ValidLocationFactory', '_signal'
    )
