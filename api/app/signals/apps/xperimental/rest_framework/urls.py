# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.urls import include, path

from signals.apps.api.generics.routers import SignalsRouter
from signals.apps.xperimental.rest_framework.viewsets.signal import PrivateSignalViewSet

router = SignalsRouter()
router.register(r'private/signals', PrivateSignalViewSet, basename='experimental-private-signals')

urlpatterns = [
    # The base routes of the experimental API
    path('experimental/', include(router.urls)),
]
