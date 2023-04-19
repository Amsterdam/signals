# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText

from signals.apps.signals.models import StatusMessage
from signals.apps.signals.workflow import STATUS_CHOICES_API


class StatusMessageFactory(DjangoModelFactory):
    title = FuzzyText(length=100)
    text = FuzzyText(length=1000)
    state = FuzzyChoice(STATUS_CHOICES_API)
    active = True

    class Meta:
        model = StatusMessage
