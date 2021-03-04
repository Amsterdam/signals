# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from factory import DjangoModelFactory, SubFactory, post_generation

from signals.apps.signals.models import CategoryAssignment


class CategoryAssignmentFactory(DjangoModelFactory):
    class Meta:
        model = CategoryAssignment

    _signal = SubFactory('signals.apps.signals.factories.signal.SignalFactory', category_assignment=None)
    category = SubFactory('signals.apps.signals.factories.category.CategoryFactory')

    @post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
