# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from factory import DjangoModelFactory, Sequence, SubFactory, fuzzy, post_generation

from signals.apps.signals.models import SignalDepartments


class SignalDepartmentsFactory(DjangoModelFactory):
    class Meta:
        model = SignalDepartments

    _signal = SubFactory('signals.apps.signals.factories.signal.SignalFactory', category_assignment=None)
    created_by = Sequence(lambda n: 'beheerder{}@example.com'.format(n))
    relation_type = fuzzy.FuzzyChoice(SignalDepartments.REL_CHOICES)

    @post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal

    @post_generation
    def departments(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            # A list of groups were passed in, use them
            for department in extracted:
                self.departments.add(department)
