from django.contrib.auth import get_user_model
from import_export import resources, fields, widgets

from signals.apps.signals.models import RoutingExpression, Expression, Department

User = get_user_model()

class RoutingExpressionResource(resources.ModelResource):
    _expression = fields.Field(
        column_name='_expression',
        attribute='_expression',
        widget=widgets.ForeignKeyWidget(Expression, 'name')
    )

    _department = fields.Field(
        column_name='_department',
        attribute='_department',
        widget=widgets.ForeignKeyWidget(Department, 'code')
    )

    _user = fields.Field(
        column_name='_user',
        attribute='_user',
        widget=widgets.ForeignKeyWidget(User, 'username')
    )

    class Meta:
        model = RoutingExpression
        import_id_fields = ('_expression',)
        exclude = ('id',)