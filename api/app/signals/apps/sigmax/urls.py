# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from django.urls import path

from signals.apps.sigmax import views

urlpatterns = [
    path('soap', views.CityControlReceiver.as_view()),
]
