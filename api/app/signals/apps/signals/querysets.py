# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.db.models import Count, F, Max, QuerySet

from signals.apps.services.domain.permissions.signal import PermissionService
from signals.apps.services.domain.permissions.utils import make_permission_condition_for_user


class SignalQuerySet(QuerySet):
    permission_service = PermissionService

    def filter_for_user(self, user):
        if not self.permission_service.has_permission(user, 'signals.sia_can_view_all_categories'):
            # We are not a superuser and we do not have the "show all categories" permission
            return self.filter(make_permission_condition_for_user(user))

        return self.all()

    def filter_reporter(self, email=None, phone=None):
        if not email and not phone:
            raise Exception('')

        qs = self.all()
        if email:
            qs = qs.filter(reporter__email__iexact=email)

        if phone:
            qs = qs.filter(reporter__phone=email)

        return qs

    def reporter_feedback_count(self, email, is_satisfied=True):
        return self.filter_reporter(
            email=email
        ).annotate(
            feedback_count=Count('feedback')
        ).filter(
            feedback_count__gte=1
        ).annotate(
            feedback_max_created_at=Max('feedback__created_at'),
            feedback_max_submitted_at=Max('feedback__submitted_at')
        ).filter(
            feedback__is_satisfied=is_satisfied,
            feedback__submitted_at__isnull=False,
            feedback__created_at=F('feedback_max_created_at'),
            feedback__submitted_at=F('feedback_max_submitted_at')
        ).count()

    def reporter_feedback_satisfied_count(self, email):
        return self.reporter_feedback_count(email=email, is_satisfied=True)

    def reporter_feedback_not_satisfied_count(self, email):
        return self.reporter_feedback_count(email=email, is_satisfied=False)
