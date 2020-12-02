from factory import DjangoModelFactory, Sequence, SubFactory

from signals.apps.signals.models import RoutingExpression


class RoutingExpressionFactory(DjangoModelFactory):
    class Meta:
        model = RoutingExpression

    _expression = SubFactory('signals.apps.signals.factories.expression.ExpressionFactory')
    _department = SubFactory('signals.apps.signals.factories.expression.DepartmentFactory')
    order = Sequence(lambda n: n)
    is_active = True
