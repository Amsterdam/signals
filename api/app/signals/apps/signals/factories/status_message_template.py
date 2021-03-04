# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from factory import DjangoModelFactory, SubFactory
from factory.fuzzy import FuzzyChoice, FuzzyText

from signals.apps.signals.models import StatusMessageTemplate
from signals.apps.signals.workflow import STATUS_CHOICES_API


class StatusMessageTemplateFactory(DjangoModelFactory):
    title = FuzzyText(length=100)
    text = FuzzyText(length=100)
    order = 0
    category = SubFactory('signals.apps.signals.factories.category.CategoryFactory')
    state = FuzzyChoice(STATUS_CHOICES_API)

    class Meta:
        model = StatusMessageTemplate
