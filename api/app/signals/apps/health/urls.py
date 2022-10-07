# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam
from django.urls import path

from signals.apps.health.rest_framework import views

urlpatterns = [
    path('health', views.health),
    path('data', views.check_data),
]
