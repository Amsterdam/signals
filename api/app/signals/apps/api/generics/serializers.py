from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import empty


class SIAModelSerializer(serializers.ModelSerializer):
    permission_classes = None

    def __init__(self, instance=None, data=empty, **kwargs):
        if 'permission_classes' in kwargs:
            self.permission_classes = kwargs.pop('permission_classes')
        super(SIAModelSerializer, self).__init__(instance=instance, data=data, **kwargs)

    def check_permissions(self):
        if not self.permission_classes:
            return

        for permission_class in self.permission_classes:
            permission = permission_class()

            request = self.context.get('request')
            view = self.context.get('view')

            if not permission.has_permission(request=request, view=view):
                raise PermissionDenied(detail=getattr(permission, 'message', None))

    def validate(self, attrs):
        """
        Will first check if the permission classes are set and of the user has the correct set of
        permission. If the permission check does not raises a PermissionDenied the parent 'validate'
        functionality is executed

        :param attrs:
        :return attrs:
        :raises PermissionDenied:
        """
        self.check_permissions()

        return super(SIAModelSerializer, self).validate(attrs=attrs)
