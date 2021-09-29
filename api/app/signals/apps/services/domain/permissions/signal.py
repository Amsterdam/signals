# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.conf import settings
from django.db.models import Q

from signals.apps.services.domain.permissions.base import PermissionService as BasePermissionService


class PermissionService(BasePermissionService):
    @staticmethod
    def _skip_permission_check(permission):
        """
        The feature flag can be used to disable the permission, by default it is enabled
        """
        flag = f'PERMISSION_{permission.upper()}'
        if hasattr(settings, 'FEATURE_FLAGS') and flag in settings.FEATURE_FLAGS:
            return not settings.FEATURE_FLAGS[flag]  # noqa Invert the flag if the check should not be skipped
        return False  # By default the permission is enabled therefore return False, check should not be skipped

    @staticmethod
    def has_permission_via_department_routing(user, signal):
        if user.is_superuser:
            return True  # With great power comes great responsibility

        if PermissionService._skip_permission_check(permission='VIA_DEPARTMENT_ROUTING'):
            return True  # The permission check is disabled therefore this method can return True

        return bool(
            set(
                user.profile.departments.values_list(
                    'pk',
                    flat=True
                )
            ).intersection(
                signal.signal_departments.filter(
                    relation_type='routing',
                ).values_list(
                    'departments__pk',
                    flat=True
                )
            )
        )

    @staticmethod
    def has_permission_via_category(user, signal):
        if user.is_superuser:
            return True  # With great power comes great responsibility

        if PermissionService._skip_permission_check(permission='VIA_CATEGORY'):
            return True  # The permission check is disabled therefore this method can return True

        return bool(
            set(
                user.profile.departments.values_list(
                    'pk',
                    flat=True
                )
            ).intersection(
                signal.category_assignment.category.departments.filter(
                    Q(categorydepartment__is_responsible=True) |
                    Q(categorydepartment__can_view=True)
                ).values_list(
                    'pk',
                    flat=True
                )
            )
        )

    @staticmethod
    def has_signal_permission(user, signal):
        if user.is_superuser:
            return True  # With great power comes great responsibility

        has_read_permission = (
                PermissionService.has_permission_via_category(user, signal) or
                PermissionService.has_permission_via_department_routing(user, signal)
        )
        return has_read_permission and PermissionService.has_permission(user, 'signals.sia_read')
