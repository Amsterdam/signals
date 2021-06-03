# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.urls import include, path

from signals.apps.api.routers import SignalsRouterVersion1
from signals.apps.questionnaires.views import (
    PrivateQuestionnaireViewSet,
    PrivateQuestionViewSet,
    PublicQuestionnaireViewSet,
    PublicQuestionViewSet,
    PublicSessionViewSet
)

router = SignalsRouterVersion1()

router.register(r'public/qa/questions', PublicQuestionViewSet, basename='public-question')
router.register(r'private/qa/questions', PrivateQuestionViewSet, basename='private-question')

router.register(r'public/qa/questionnaires', PublicQuestionnaireViewSet, basename='public-questionnaire')
router.register(r'private/qa/questionnaires', PrivateQuestionnaireViewSet, basename='private-questionnaire')

router.register(r'public/qa/sessions', PublicSessionViewSet, basename='public-session')

urlpatterns = [
    path('', include((router.urls, 'signals.apps.questionnaires'), namespace='questionnaires')),
]
