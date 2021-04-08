# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText

from signals.apps.signals.models import Expression, ExpressionContext, ExpressionType


class ExpressionTypeFactory(DjangoModelFactory):
    class Meta:
        model = ExpressionType

    name = Sequence(lambda n: f'type_{n}')
    description = Sequence(lambda n: f'Omschrijving voor expressie type_{n}')


class ExpressionFactory(DjangoModelFactory):
    name = FuzzyText(length=3)
    code = FuzzyText(length=100)
    _type = SubFactory(ExpressionTypeFactory)

    class Meta:
        model = Expression


class ExpressionContextFactory(DjangoModelFactory):
    class Meta:
        model = ExpressionContext

    identifier = Sequence(lambda n: f'ident_{n}')
    identifier_type = FuzzyChoice(choices=list(dict(ExpressionContext.CTX_TYPE_CHOICES).keys()))
    _type = SubFactory(ExpressionTypeFactory)
