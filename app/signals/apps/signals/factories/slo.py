# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from django.utils import timezone
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyDateTime, FuzzyInteger

from signals.apps.signals.models import ServiceLevelObjective


class ServiceLevelObjectiveFactory(DjangoModelFactory):
    class Meta:
        model = ServiceLevelObjective

    category = SubFactory('signals.apps.signals.factories.category.CategoryFactory')
    n_days = FuzzyInteger(3, 7)
    use_calendar_days = FuzzyChoice((True, False))
    created_by = Sequence(lambda n: 'beheerder{}@example.com'.format(n))
    created_at = FuzzyDateTime(timezone.now())
