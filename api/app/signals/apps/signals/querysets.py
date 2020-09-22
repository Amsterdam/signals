from django.db.models import Q, QuerySet


class SignalQuerySet(QuerySet):
    def filter_for_user(self, user):
        if not user.is_superuser and not user.has_perm('signals.sia_can_view_all_categories'):
            # We are not a superuser and we do not have the "show all categories" permission
            category_ids = user.profile.departments.prefetch_related(
                'categorydepartment_set'
            ).filter(
                Q(categorydepartment__is_responsible=True) |
                Q(categorydepartment__can_view=True)
            ).values_list(
                'categorydepartment__category_id',
                flat=True
            )

            department_ids = user.profile.departments.values_list('id', flat=True)

            return self.filter(
                Q(category_assignment__category_id__in=category_ids) |
                (
                    Q(signal_departments__relation_type='routing') &
                    Q(signal_departments__departments__id__in=department_ids)
                )
            )

        return self.all()
