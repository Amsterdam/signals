from import_export import resources

from signals.apps.signals.models import Department


class DepartmentResource(resources.ModelResource):
    # TODO: Categorieën mee exporteren en importeren, incl can_view en is_responsible veld?

    class Meta:
        model = Department
