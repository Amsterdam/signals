# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
import factory
from django.utils import timezone
from factory import fuzzy

from signals.apps.sigmax.models import CityControlRoundtrip


class CityControlRoundtripFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CityControlRoundtrip
        skip_postgeneration_save = True

    _signal: factory.SubFactory = factory.SubFactory('signals.apps.signals.factories.SignalFactory')
    when = fuzzy.FuzzyDateTime(timezone.now())
