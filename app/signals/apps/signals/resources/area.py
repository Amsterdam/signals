from import_export import resources, fields, widgets

from signals.apps.signals.models import Area, AreaType


class AreaResource(resources.ModelResource):
    _type = fields.Field(
        column_name='_type',
        attribute='_type',
        widget=widgets.ForeignKeyWidget(AreaType, 'code')
    )

    class Meta:
        model = Area