from rest_framework.relations import PrimaryKeyRelatedField

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.signals.models import Department, SignalDepartments


def _get_department_queryset():
    return Department.objects.all()


class _NestedDepartmentModelSerializer(SIAModelSerializer):
    id = PrimaryKeyRelatedField(required=False, queryset=_get_department_queryset())

    class Meta:
        model = Department
        fields = (
            'id',
            'code',
            'name',
            'is_intern',
        )
        read_only_fields = (
            'id',
            'code',
            'name',
            'is_intern',
        )


class _NestedSignalDepartmentsModelSerializer(SIAModelSerializer):
    departments = _NestedDepartmentModelSerializer(
        many=True,
        required=False,
        permission_classes=(SIAPermissions,),
    )

    class Meta:
        model = SignalDepartments
        fields = (
            'relation_type',
            'created_by',
            'departments',
        )
