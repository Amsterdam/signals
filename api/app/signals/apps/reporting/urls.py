# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.urls import include, path

from signals.apps.api.generics.routers import SignalsRouter
from signals.apps.reporting.rest_framework.views import PrivateReportViewSet

router = SignalsRouter()

router.register(r'private/reports', PrivateReportViewSet, basename='private-reports')


urlpatterns = [
    path('', include((router.urls, 'signals.apps.reporting'), namespace='reporting')),
]
