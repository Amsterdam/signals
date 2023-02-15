# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from string import digits

from factory import Sequence, SubFactory, post_generation
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from signals.apps.signals.models import Reporter


class ReporterFactory(DjangoModelFactory):

    class Meta:
        model = Reporter

    _signal = SubFactory('signals.apps.signals.factories.signal.SignalFactory', reporter=None)

    email = Sequence(lambda n: 'veelmelder{}@example.com'.format(n))
    email_anonymized = False

    phone = FuzzyText(length=10, chars=digits)
    phone_anonymized = False

    @post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
