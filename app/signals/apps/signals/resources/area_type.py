from import_export import resources

from signals.apps.signals.models import AreaType


class AreaTypeResource(resources.ModelResource):
    class Meta:
        model = AreaType
        import_id_fields = ('code',)
        exclude = ('id',)