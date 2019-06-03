from rest_framework import routers

from signals.apps.feedback.views import FeedbackViewSet, StandardAnswerViewSet

feedback_router = routers.SimpleRouter()
feedback_router.register(
    r'standard_answers', StandardAnswerViewSet, basename='feedback-standard-answers')
feedback_router.register(r'forms', FeedbackViewSet, basename='feedback-forms')
