# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import os

from django.urls import include, path
from django.views.generic.base import TemplateView

from signals.apps.api.generics.routers import SignalsRouter
from signals.apps.questionnaires.rest_framework.views import (
    PublicQuestionnaireViewSet,
    PublicQuestionViewSet,
    PublicSessionViewSet
)

router = SignalsRouter()

router.register(r'public/qa/questions', PublicQuestionViewSet, basename='public-question')
router.register(r'public/qa/questionnaires', PublicQuestionnaireViewSet, basename='public-questionnaire')
router.register(r'public/qa/sessions', PublicSessionViewSet, basename='public-session')

urlpatterns = [
    path('', include((router.urls, 'signals.apps.questionnaires'), namespace='questionnaires')),

    # Swagger documentation for the public endpoints
    path('public/qa/swagger/openapi.yaml',
         TemplateView.as_view(template_name='questionnaires/swagger/public_openapi.yaml',
                              extra_context={'schema_url': 'openapi-schema',
                                             'global_api_root': os.getenv('global_api_root', None)}),
         name='swagger-ui'),
]
