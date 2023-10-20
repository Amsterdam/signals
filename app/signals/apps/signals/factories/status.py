# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from factory import Sequence, SubFactory, post_generation
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText

from signals.apps.signals.models import Status
from signals.apps.signals.workflow import GEMELD


class StatusFactory(DjangoModelFactory):

    class Meta:
        model = Status
        skip_postgeneration_save = True

    _signal: SubFactory = SubFactory('signals.apps.signals.factories.signal.SignalFactory', status=None)

    text = FuzzyText(length=400)
    user = Sequence(lambda n: 'veelmelder{}@example.com'.format(n))
    state = GEMELD  # Initial state is always 'm'
    extern: FuzzyChoice = FuzzyChoice((True, False))

    @post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
        self.save()
