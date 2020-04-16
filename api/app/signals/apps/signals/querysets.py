from django.db.models import Q, QuerySet


class SignalQuerySet(QuerySet):
    def filter_for_user(self, user):
        if not user.is_superuser and not user.has_perm('signals.sia_can_view_all_categories'):
            # We are not a superuser and we do not have the "show all categories" permission
            return self.filter(
                Q(category_assignment__category__categorydepartment__is_responsible=True) |
                Q(category_assignment__category__categorydepartment__can_view=True),
                category_assignment__category__departments__in=list(
                    user.profile.departments.values_list('pk', flat=True)
                )
            ).distinct()

        return self.all()
