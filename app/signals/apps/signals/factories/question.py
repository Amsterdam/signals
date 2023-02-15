# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText

from signals.apps.signals.models import Question


class QuestionFactory(DjangoModelFactory):
    key = FuzzyText(length=3)
    field_type = FuzzyChoice(choices=list(dict(Question.FIELD_TYPE_CHOICES).keys()))
    meta = '{ "dummy" : "test" }'
    required = FuzzyChoice(choices=[True, False])

    class Meta:
        model = Question
