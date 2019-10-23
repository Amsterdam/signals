from datapunt_api.rest import HALSerializer
from datapunt_api.serializers import DisplayField
from django.contrib.auth.models import Permission


class PermissionSerializer(HALSerializer):
    _display = DisplayField()

    class Meta:
        model = Permission
        fields = (
            '_links',
            '_display',
            'id',
            'name',
            'codename',
        )
