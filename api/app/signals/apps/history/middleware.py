# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from signals.apps.history.services import CategoryLogService
from signals.apps.history.services.history_log import HistoryLogService


class HistoryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        CategoryLogService.thread.request = request
        HistoryLogService.thread.request = request
        return self.get_response(request)
