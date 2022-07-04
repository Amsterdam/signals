# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.core.handlers.wsgi import WSGIRequest
from django.utils import timezone

from signals.apps.history.models import Log


class HistoryLogService:

    @staticmethod
    def log_update(request: WSGIRequest, instance) -> None:
        if not hasattr(instance, 'changed_data') or not callable(instance.changed_data):
            return

        changed_data = instance.changed_data()
        if changed_data:
            if request and request.user:
                created_by = request.user.username
            else:
                created_by = None

            instance.history_log.create(
                action=Log.ACTION_UPDATE,
                created_by=created_by,
                created_at=timezone.now(),
                data=changed_data
            )
