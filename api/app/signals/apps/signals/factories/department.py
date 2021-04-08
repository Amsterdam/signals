# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from string import ascii_uppercase

from factory import LazyFunction
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText
from faker import Faker

from signals.apps.signals.models import Department

fake = Faker()


class DepartmentFactory(DjangoModelFactory):
    code = FuzzyText(length=3, chars=ascii_uppercase)
    name = LazyFunction(lambda: ' '.join(fake.words(nb=3)))
    is_intern = FuzzyChoice(choices=[True, False])
    can_direct = FuzzyChoice(choices=[True, False])

    class Meta:
        model = Department
