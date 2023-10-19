# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from factory import SubFactory, post_generation
from factory.django import DjangoModelFactory

from signals.apps.signals.models import CategoryAssignment


class CategoryAssignmentFactory(DjangoModelFactory):
    class Meta:
        model = CategoryAssignment
        skip_postgeneration_save = True

    _signal: SubFactory = SubFactory('signals.apps.signals.factories.signal.SignalFactory', category_assignment=None)
    category: SubFactory = SubFactory('signals.apps.signals.factories.category.CategoryFactory')

    @post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
        self.save()
