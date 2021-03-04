# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from factory import DjangoModelFactory, SubFactory, post_generation

from signals.apps.signals.models import Priority


class PriorityFactory(DjangoModelFactory):

    class Meta:
        model = Priority

    _signal = SubFactory('signals.apps.signals.factories.signal.SignalFactory', priority=None)

    @post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
