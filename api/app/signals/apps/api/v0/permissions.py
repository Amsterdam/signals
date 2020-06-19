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
