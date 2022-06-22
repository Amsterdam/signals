# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import threading

from django.utils import timezone

from signals.apps.history.models import Log


class HistoryLogService:
    thread = threading.local()

    @staticmethod
    def log_update(instance) -> None:
        changed_data = instance.changed_data()
        if changed_data:
            if HistoryLogService.thread.request and HistoryLogService.thread.request.user:
                created_by = HistoryLogService.thread.request.user.username
            else:
                created_by = None

            instance.history_log.create(
                action=Log.ACTION_UPDATE,
                created_by=created_by,
                created_at=timezone.now(),
                data=changed_data
            )
