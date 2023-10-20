# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from factory import Sequence, SubFactory, post_generation
from factory.django import DjangoModelFactory

from signals.apps.signals.models import SignalDepartments


class SignalDepartmentsFactory(DjangoModelFactory):
    class Meta:
        model = SignalDepartments
        skip_postgeneration_save = True

    _signal: SubFactory = SubFactory('signals.apps.signals.factories.signal.SignalFactory', category_assignment=None)
    created_by = Sequence(lambda n: 'beheerder{}@example.com'.format(n))
    relation_type = SignalDepartments.REL_DIRECTING

    @post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
        self.save()

    @post_generation
    def departments(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            # A list of groups were passed in, use them
            for department in extracted:
                self.departments.add(department)
            self.save()
