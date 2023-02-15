# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
class PermissionService:
    @staticmethod
    def has_permission(user, permission, signal=None):
        if user.is_superuser:
            return True  # With great power comes great responsibility

        return user.has_perm(permission, obj=signal)

    @staticmethod
    def has_permissions(user, permissions, signal=None):
        if user.is_superuser:
            return True  # With great power comes great responsibility

        return user.has_perms(permissions, obj=signal)
