# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from factory import SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText

from signals.apps.signals.models import StoredSignalFilter


class StoredSignalFilterFactory(DjangoModelFactory):
    name = FuzzyText(length=100)
    created_by = SubFactory('signals.apps.users.factories.UserFactory')
    refresh = FuzzyChoice((True, False))

    class Meta:
        model = StoredSignalFilter
