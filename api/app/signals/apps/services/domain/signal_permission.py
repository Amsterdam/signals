from django.db.models import Q


class SignalPermissionService:

    def make_permisson_condition(self, user):
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

        return (
            Q(category_assignment__category_id__in=category_ids) |
            (
                Q(signal_departments__relation_type='routing') &
                Q(signal_departments__departments__id__in=department_ids)
            )
        )

    def has_permission_via_routing(self, user, signal):
        if not hasattr(signal, 'signal_departments'):
            return False

        has_read_permission_via_routing = set(
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

        return bool(has_read_permission_via_routing)

    def has_permission_via_category(self, user, signal):
        has_category_read_permission = set(
            user.profile.departments.values_list(
                'pk',
                flat=True
            )
        ).intersection(
            signal.category_assignment.category.departments.filter(
                categorydepartment__can_view=True
            ).values_list(
                'pk',
                flat=True
            )
        )
        return bool(has_category_read_permission)
