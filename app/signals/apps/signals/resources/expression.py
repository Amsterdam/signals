from import_export import resources, fields, widgets

from signals.apps.signals.models import Expression, ExpressionType


class ExpressionResource(resources.ModelResource):
    _type = fields.Field(
        column_name='_type',
        attribute='_type',
        widget=widgets.ForeignKeyWidget(ExpressionType, 'name')
    )

    # TODO: Linken via import / export aan bijbehorende RoutingExpression?

    class Meta:
        model = Expression
