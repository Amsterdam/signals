# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory

from signals.apps.signals.models import CategoryQuestion


class CategoryQuestionFactory(DjangoModelFactory):
    class Meta:
        model = CategoryQuestion
        skip_postgeneration_save = True

    category: SubFactory = SubFactory('signals.apps.signals.factories.category.CategoryFactory')
    question: SubFactory = SubFactory('signals.apps.signals.factories.question.QuestionFactory')
    order = Sequence(lambda n: n)
