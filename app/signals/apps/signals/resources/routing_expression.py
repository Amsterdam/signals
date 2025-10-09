from import_export import resources

from signals.apps.signals.models import RoutingExpression


class RoutingExpressionResource(resources.ModelResource):
    # TODO: importeer / exporteer _user
    # TODO: importeer / exporteer _department
    # TODO: importeer / exporteer _expression

    class Meta:
        model = RoutingExpression
