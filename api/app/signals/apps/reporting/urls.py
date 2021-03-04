# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.urls import path

from signals.apps.reporting import views

urlpatterns = [
    path('horeca_csv', views.HorecaCSVExportViewSet.as_view({'get': 'list'})),
]
