# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from factory import SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

from signals.apps.signals.models import CategoryDepartment


class CategoryDepartmentFactory(DjangoModelFactory):
    class Meta:
        model = CategoryDepartment
        skip_postgeneration_save = True

    category: SubFactory = SubFactory('signals.apps.signals.factories.category.CategoryFactory')
    department: SubFactory = SubFactory('signals.apps.signals.factories.department.DepartmentFactory')

    is_responsible: FuzzyChoice = FuzzyChoice((True, False))
    can_view: FuzzyChoice = FuzzyChoice((True, False))
