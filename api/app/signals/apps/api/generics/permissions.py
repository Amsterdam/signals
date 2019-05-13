from rest_framework import exceptions
from rest_framework.permissions import BasePermission


class StatusPermission(BasePermission):
    """Permission check for `Status`."""

    def has_permission(self, request, view):
        if request.user:
            if request.method == 'POST' and not request.user.has_perm('signals.add_status'):
                return False
            return True
        else:
            return False


class CategoryPermission(BasePermission):
    """Permission check for `Category`."""

    def has_permission(self, request, view):
        if request.user:
            if (request.method == 'POST' and
                    not request.user.has_perm('signals.add_categoryassignment')):
                return False
            return True
        else:
            return False


class LocationPermission(BasePermission):
    """Permission check for `Location`."""

    def has_permission(self, request, view):
        if request.user:
            if request.method == 'POST' and not request.user.has_perm('signals.add_location'):
                return False
            return True
        else:
            return False


class PriorityPermission(BasePermission):
    """Permission check for `Priority`."""

    def has_permission(self, request, view):
        if request.user:
            if request.method == 'POST' and not request.user.has_perm('signals.add_priority'):
                return False
            return True
        else:
            return False


class NotePermission(BasePermission):
    """Permission check for `Note`."""

    def has_permission(self, request, view):
        if request.user:
            if request.method == 'POST' and not request.user.has_perm('signals.add_note'):
                return False
            return True
        else:
            return False


class SIAPermissions(BasePermission):
    perms_map = {
        'GET': ['signals.sia_read'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['signals.sia_write'],
        'PUT': ['signals.sia_write'],
        'PATCH': ['signals.sia_write'],
        'DELETE': ['signals.sia_write'],
    }

    def get_required_permissions(self, method):
        if method not in self.perms_map:
            raise exceptions.MethodNotAllowed(method)

        return self.perms_map[method]

    def has_permission(self, request, view):
        if request.user:
            perms = self.get_required_permissions(method=request.method)
            return request.user.has_perms(perms)
        return False
