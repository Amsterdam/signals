# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam
from django.urls import path

from signals.apps.sigmax.rest_framework.views import CityControlReceiver

urlpatterns = [
    path('soap', CityControlReceiver.as_view()),
]
