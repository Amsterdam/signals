# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.urls import include, path

from signals.apps.api.routers import SignalsRouterVersion1
from signals.apps.reports.rest_framework.views import PrivateReportViewSet

router = SignalsRouterVersion1()

router.register(r'private/reports', PrivateReportViewSet, basename='private-reports')


urlpatterns = [
    path('', include((router.urls, 'signals.apps.reports'), namespace='reports')),
]
