# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from signals.apps.signals.models import Buurt


class BuurtFactory(DjangoModelFactory):
    class Meta:
        model = Buurt
        skip_postgeneration_save = True

    id = FuzzyText(length=14)
    vollcode = FuzzyText(length=4)
    naam = FuzzyText(length=40)
