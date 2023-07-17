# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.urls import include, path

from signals.apps.api.generics.routers import SignalsRouter
from signals.apps.feedback.rest_framework.views import FeedbackViewSet, StandardAnswerViewSet

router = SignalsRouter()
router.register(r'public/feedback/standard_answers', StandardAnswerViewSet, basename='feedback-standard-answers')
router.register(r'public/feedback/forms', FeedbackViewSet, basename='feedback-forms')

urlpatterns = [
    path('', include((router.urls, 'signals.apps.feedback'), namespace='feedback')),
]
