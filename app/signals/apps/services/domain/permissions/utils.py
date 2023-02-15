# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.db.models import Q


def make_permission_condition_for_user_by_category(user):
    return Q(category_assignment__category_id__in=user.profile.departments.prefetch_related(
        'categorydepartment_set'
    ).filter(
        Q(categorydepartment__is_responsible=True) |
        Q(categorydepartment__can_view=True)
    ).values_list(
        'categorydepartment__category_id',
        flat=True
    ))


def make_permission_condition_for_user_by_department_routing(user):
    return Q(routing_assignment__departments__id__in=user.profile.departments.values_list('id', flat=True))


def make_permission_condition_for_user(user):
    return (
        make_permission_condition_for_user_by_category(user) |
        make_permission_condition_for_user_by_department_routing(user)
    )
