# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2022 Gemeente Amsterdam
from factory import SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText

from signals.apps.signals.models import StatusMessageTemplate
from signals.apps.signals.workflow import STATUS_CHOICES_API


class StatusMessageTemplateFactory(DjangoModelFactory):
    title = FuzzyText(length=100)
    text = FuzzyText(length=100)
    order = 0
    category = SubFactory('signals.apps.signals.factories.category.CategoryFactory')
    state = FuzzyChoice(STATUS_CHOICES_API)
    is_active = True

    class Meta:
        model = StatusMessageTemplate
