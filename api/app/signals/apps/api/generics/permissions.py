from django.conf import settings
from rest_framework import exceptions
from rest_framework.permissions import BasePermission, DjangoModelPermissions

from signals.apps.services.domain.signal_permission import SignalPermissionService


class SIABasePermission(BasePermission):
    perms_map = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],
        'POST': [],
        'PUT': [],
        'PATCH': [],
        'DELETE': [],
    }

    def _skip_permission_check(self):
        """
        The feature flag can be used to disable the permission, by default it is enabled
        So if we need to skip it we need to inverse the feature_flag setting
        """
        flag = 'PERMISSION_{}'.format(self.__class__.__name__.upper())
        return not settings.FEATURE_FLAGS[flag] if flag in settings.FEATURE_FLAGS else False

    def get_required_permissions(self, method):
        if method not in self.perms_map:
            raise exceptions.MethodNotAllowed(method)

        return self.perms_map[method]

    def has_permission(self, request, *args, **kwargs):
        if request.user:
            if self._skip_permission_check():
                return True

            perms = self.get_required_permissions(method=request.method)
            return request.user.has_perms(perms)
        else:
            return False


class SIAPermissions(SIABasePermission):
    perms_map = {
        'GET': ['signals.sia_read'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['signals.sia_write'],
        'PUT': ['signals.sia_write'],
        'PATCH': ['signals.sia_write'],
        'DELETE': ['signals.sia_write'],
    }


class SignalCreateInitialPermission(SIABasePermission):
    perms_map = {
        'GET': ['signals.sia_read'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['signals.sia_write', 'signals.sia_signal_create_initial'],
        'PUT': ['signals.sia_write'],
        'PATCH': ['signals.sia_write'],
    }


class SignalCreateNotePermission(SIABasePermission):
    perms_map = {
        'GET': ['signals.sia_read'],
        'OPTIONS': [],
        'HEAD': [],
        'PUT': ['signals.sia_write', 'signals.sia_signal_create_note'],
        'PATCH': ['signals.sia_write', 'signals.sia_signal_create_note'],
    }


class SignalChangeStatusPermission(SIABasePermission):
    perms_map = {
        'GET': ['signals.sia_read'],
        'OPTIONS': [],
        'HEAD': [],
        'PUT': ['signals.sia_write', 'signals.sia_signal_change_status'],
        'PATCH': ['signals.sia_write', 'signals.sia_signal_change_status'],
    }


class SignalChangeCategoryPermission(SIABasePermission):
    perms_map = {
        'GET': ['signals.sia_read'],
        'OPTIONS': [],
        'HEAD': [],
        'PUT': ['signals.sia_write', 'signals.sia_signal_change_category'],
        'PATCH': ['signals.sia_write', 'signals.sia_signal_change_category'],
    }


class ModelWritePermissions(DjangoModelPermissions):
    """
    In SIA we have binary permissions instead of the default add, change, delete permissions
    provided by Django.
    The 2 permissions are:
        * sia_read
        * sia_{model_name}_write
    """
    perms_map = {
        'GET': ['signals.sia_read'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.sia_%(model_name)s_write'],
        'PUT': ['%(app_label)s.sia_%(model_name)s_write'],
        'PATCH': ['%(app_label)s.sia_%(model_name)s_write'],
        'DELETE': ['%(app_label)s.sia_%(model_name)s_write'],
    }


class SignalViewObjectPermission(DjangoModelPermissions):
    permission_service = SignalPermissionService()

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.has_perm('signals.sia_can_view_all_categories'):  # noqa
            return True

        read_permisson = (
            self.permission_service.has_permission_via_category(request.user, obj) or
            self.permission_service.has_permission_via_routing(request.user, obj)
        )

        return read_permisson and request.user.has_perm('signals.sia_read')


class SIAReportPermissions(SIABasePermission):
    perms_map = {
        'GET': ['signals.sia_read', 'signals.sia_signal_report'],
        'OPTIONS': [],
        'HEAD': []
    }
