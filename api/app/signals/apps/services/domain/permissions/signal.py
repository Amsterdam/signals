# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.conf import settings
from django.db.models import Q

from signals.apps.services.domain.permissions.base import PermissionService


class SignalPermissionService(PermissionService):
    @staticmethod
    def _skip_permission_check(permission):
        """
        The feature flag can be used to disable the permission, by default the permission check is enabled
        """
        flag = f'SKIP_PERMISSION_{permission.upper()}'
        if hasattr(settings, 'FEATURE_FLAGS') and flag in settings.FEATURE_FLAGS:
            return settings.FEATURE_FLAGS[flag]
        return False  # By default the permission check is enabled therefore return False

    @staticmethod
    def has_permission_via_department_routing(user, signal):
        if user.is_superuser:
            return True  # With great power comes great responsibility

        if SignalPermissionService._skip_permission_check(permission='VIA_DEPARTMENT_ROUTING'):
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

        if SignalPermissionService._skip_permission_check(permission='VIA_CATEGORY'):
            return True  # The permission check is disabled therefore this method can return True

        return bool(
            set(
                user.profile.departments.values_list(
                    'pk',
                    flat=True
                )
            ).intersection(
                signal.category_assignment.category.departments.filter(
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
                SignalPermissionService.has_permission_via_category(user, signal) or
                SignalPermissionService.has_permission_via_department_routing(user, signal)
        )
        return has_read_permission and SignalPermissionService.has_permission(user, 'signals.sia_read')
