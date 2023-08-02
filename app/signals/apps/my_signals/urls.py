# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 -2023 Gemeente Amsterdam
from django.urls import include, path

from signals.apps.api.generics.routers import SignalsRouter
from signals.apps.my_signals.rest_framework.views.me import MySignalsLoggedInReporterView
from signals.apps.my_signals.rest_framework.views.signals import MySignalsViewSet
from signals.apps.my_signals.rest_framework.views.token import ObtainMySignalsTokenViewSet

router = SignalsRouter()

router.register(r'my/signals', MySignalsViewSet, basename='my-signals')

urlpatterns = [
    path('my/signals/request-auth-token', ObtainMySignalsTokenViewSet.as_view()),
    path('my/signals/me', MySignalsLoggedInReporterView.as_view()),
    path('', include((router.urls, 'signals.apps.my_signals'), namespace='my_signals')),
]
