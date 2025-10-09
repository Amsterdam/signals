from import_export import resources, fields, widgets

from signals.apps.signals.models import Expression, ExpressionType


class ExpressionResource(resources.ModelResource):
    _type = fields.Field(
        column_name='_type',
        attribute='_type',
        widget=widgets.ForeignKeyWidget(ExpressionType, 'name')
    )

    class Meta:
        model = Expression
        import_id_fields = ('code',)
        exclude = ('id',)
