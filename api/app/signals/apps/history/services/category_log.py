# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import threading

from django.utils import timezone

from signals.apps.history.models import Log


class CategoryLogService:
    thread = threading.local()

    @staticmethod
    def log_update(category) -> None:
        changed_data = category.changed_data()
        if changed_data:
            if CategoryLogService.thread.request and CategoryLogService.thread.request.user:
                created_by = CategoryLogService.thread.request.user.username
            else:
                created_by = None

            category.history_log.create(
                action=Log.ACTION_UPDATE,
                created_by=created_by,
                created_at=timezone.now(),
                data=changed_data
            )
