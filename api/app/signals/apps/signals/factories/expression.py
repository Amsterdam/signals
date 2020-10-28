import factory
from factory import fuzzy

from signals.apps.signals.models import Expression, ExpressionContext, ExpressionType


class ExpressionTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExpressionType

    name = factory.Sequence(lambda n: f'type_{n}')
    description = factory.Sequence(lambda n: f'Omschrijving voor expressie type_{n}')


class ExpressionFactory(factory.DjangoModelFactory):
    name = fuzzy.FuzzyText(length=3)
    code = fuzzy.FuzzyText(length=100)
    _type = factory.SubFactory(ExpressionTypeFactory)

    class Meta:
        model = Expression


class ExpressionContextFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExpressionContext

    identifier = factory.Sequence(lambda n: f'ident_{n}')
    identifier_type = fuzzy.FuzzyChoice(choices=list(dict(ExpressionContext.CTX_TYPE_CHOICES).keys()))
    _type = factory.SubFactory(ExpressionTypeFactory)
