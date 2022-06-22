# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from signals.apps.history.services import HistoryLogService


class HistoryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        paths = ['/signals/v1/private/categories/', '/signals/v1/private/users/', '/signals/admin/auth/user/',
                 '/signals/admin/signals/category/', ]
        if request.method in ['PUT', 'PATCH', 'POST'] and any(map(request.path.startswith, paths)):
            # Only add the request to the thread when changing a Category OR a User instance
            #
            # Created ticket SIG-4657 on the Amsterdam JIRA backlog to find a better solution than using threading for
            # this.
            HistoryLogService.thread.request = request

        return self.get_response(request)
