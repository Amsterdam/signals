# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.urls import include, path

from signals.apps.api.routers import SignalsRouterVersion1
from signals.apps.questionnaires.views import (
    PrivateQuestionnaireViewSet,
    PrivateQuestionViewSet,
    PublicQuestionnaireViewSet,
    PublicQuestionViewSet
)

router = SignalsRouterVersion1()

router.register(r'public/question', PublicQuestionViewSet, basename='public-question')
router.register(r'private/question', PrivateQuestionViewSet, basename='private-question')

router.register(r'public/questionnaires', PublicQuestionnaireViewSet, basename='public-questionnaire')
router.register(r'private/questionnaires', PrivateQuestionnaireViewSet, basename='private-questionnaire')

urlpatterns = [
    path('', include((router.urls, 'signals.apps.questionnaires'), namespace='questionnaires')),
]
