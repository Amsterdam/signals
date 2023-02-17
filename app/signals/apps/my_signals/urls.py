# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import os

from django.urls import include, path
from django.views.generic.base import TemplateView

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

    # Swagger documentation for the public endpoints
    path('my/signals/swagger/openapi.yaml',
         TemplateView.as_view(template_name='my_signals/swagger/public_openapi.yaml',
                              extra_context={'schema_url': 'openapi-schema',
                                             'global_api_root': os.getenv('global_api_root', None)}),
         name='swagger-ui'),
]
