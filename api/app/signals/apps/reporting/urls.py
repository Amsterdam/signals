# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.urls import include, path

from signals.apps.api.routers import SignalsRouterVersion1
# from signals.apps.reporting import views
from signals.apps.reporting.rest_framework.views import PrivateReportViewSet

router = SignalsRouterVersion1()

router.register(r'private/reports', PrivateReportViewSet, basename='private-reports')


urlpatterns = [
    path('', include((router.urls, 'signals.apps.reporting'), namespace='reporting')),
    # path('horeca_csv', views.HorecaCSVExportViewSet.as_view({'get': 'list'})),
]
