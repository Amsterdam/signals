from django.db.models import QuerySet

from signals.apps.services.domain.signal_permission import SignalPermissionService


class SignalQuerySet(QuerySet):
    permission_service = SignalPermissionService()

    def filter_for_user(self, user):
        if not user.is_superuser and not user.has_perm('signals.sia_can_view_all_categories'):
            # We are not a superuser and we do not have the "show all categories" permission
            return self.filter(self.permission_service.make_permisson_condition_for_user(user))

        return self.all()
