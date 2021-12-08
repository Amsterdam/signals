# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.db.models import QuerySet

from signals.apps.services.domain.permissions.signal import SignalPermissionService
from signals.apps.services.domain.permissions.utils import make_permission_condition_for_user


class SignalFilterViewQuerySet(QuerySet):
    permission_service = SignalPermissionService

    def filter_for_user(self, user):
        """
        Enforce all permission rules

        Code copied from signals.apps.services.domain.permissions.utils.make_permission_condition_for_user
        Small adjustment so that it can work with the database view signals_filter_view
        """
        if self.permission_service.has_permission(user, 'signals.sia_can_view_all_categories'):
            # The user has the "show all categories" permission OR is a superuser
            return self.all()

        return self.filter(make_permission_condition_for_user(user))
