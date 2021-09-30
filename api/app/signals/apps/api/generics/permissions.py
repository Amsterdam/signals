# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from rest_framework import exceptions
from rest_framework.permissions import BasePermission, DjangoModelPermissions

from signals.apps.services.domain.permissions.signal import SignalPermissionService


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

    def get_required_permissions(self, method):
        if method not in self.perms_map:
            raise exceptions.MethodNotAllowed(method)
        return self.perms_map[method]

    def has_permission(self, request, *args, **kwargs):
        if not request.user:
            return False
        permissions = self.get_required_permissions(method=request.method)
        return SignalPermissionService.has_permissions(request.user, permissions)


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
    permission_service = SignalPermissionService

    def has_object_permission(self, request, view, obj):
        if self.permission_service.has_permission(request.user, 'signals.sia_can_view_all_categories'):
            return True
        return self.permission_service.has_signal_permission(request.user, obj)


class SIAReportPermissions(SIABasePermission):
    perms_map = {
        'GET': ['signals.sia_read', 'signals.sia_signal_report'],
        'OPTIONS': [],
        'HEAD': []
    }


class SIAUserPermissions(SIABasePermission):
    perms_map = {
        'GET': ['signals.sia_read', 'auth.view_user'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['signals.sia_write', 'auth.add_user'],
        'PUT': ['signals.sia_write', 'auth.change_user'],
        'PATCH': ['signals.sia_write', 'auth.change_user'],
        'DELETE': ['signals.sia_write', 'auth.delete_user'],
    }
