from rest_framework import serializers

from signals.apps.signals.models import Department
from signals.apps.users.models import Profile


def _get_departments_queryset():
    return Department.objects.all()


class ProfileListSerializer(serializers.ModelSerializer):
    departments = serializers.SerializerMethodField()
    department_ids = serializers.PrimaryKeyRelatedField(
        many=True, required=False, read_only=False, write_only=True,
        queryset=_get_departments_queryset(), source='departments'
    )

    class Meta:
        model = Profile
        fields = (
            'note',
            'departments',
            'department_ids',
            'created_at',
            'updated_at',
        )

    def get_departments(self, obj):
        return obj.departments.values_list('name', flat=True)


class ProfileDetailSerializer(serializers.ModelSerializer):
    departments = serializers.SerializerMethodField()
    department_ids = serializers.PrimaryKeyRelatedField(
        many=True, required=False, read_only=False, write_only=True,
        queryset=_get_departments_queryset(), source='departments'
    )

    class Meta:
        model = Profile
        fields = (
            'note',
            'departments',
            'department_ids',
            'created_at',
            'updated_at',
        )

    def get_departments(self, obj):
        return obj.departments.values_list('name', flat=True)
