from rest_framework import permissions


class StatusPermission(permissions.BasePermission):
    """Permission check for `Status`."""

    def has_permission(self, request, view):
        if request.user:
            if request.method == 'POST' and not request.user.has_perm('signals.add_status'):
                return False
            return True
        else:
            return False


class CategoryPermission(permissions.BasePermission):
    """Permission check for `Category`."""

    def has_permission(self, request, view):
        if request.user:
            if request.method == 'POST' and not request.user.has_perm('signals.add_category'):
                return False
            return True
        else:
            return False


class LocationPermission(permissions.BasePermission):
    """Permission check for `Location`."""

    def has_permission(self, request, view):
        if request.user:
            if request.method == 'POST' and not request.user.has_perm('signals.add_location'):
                return False
            return True
        else:
            return False


class PriorityPermission(permissions.BasePermission):
    """Permission check for `Priority`."""

    def has_permission(self, request, view):
        if request.user:
            if request.method == 'POST' and not request.user.has_perm('signals.add_priority'):
                return False
            return True
        else:
            return False
