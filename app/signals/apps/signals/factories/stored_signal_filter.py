# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from factory import SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText

from signals.apps.signals.models import StoredSignalFilter


class StoredSignalFilterFactory(DjangoModelFactory):
    name = FuzzyText(length=100)
    created_by: SubFactory = SubFactory('signals.apps.users.factories.UserFactory')
    refresh :FuzzyChoice = FuzzyChoice((True, False))
    show_on_overview = False

    class Meta:
        model = StoredSignalFilter
        skip_postgeneration_save = True
