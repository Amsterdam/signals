"""
Views for feedback handling.
"""
from datapunt_api.pagination import HALPagination
from django.utils import timezone
from django.views.generic.detail import SingleObjectMixin
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_410_GONE

from signals.apps.feedback.exceptions import Gone
from signals.apps.feedback.models import Feedback, StandardAnswer
from signals.apps.feedback.serializers import (
    FeedbackSerializer,
    StandardAnswerSerializer,
)


class StandardAnswerViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """View to list all currently visible Standard Answers."""
    serializer_class = StandardAnswerSerializer
    queryset = StandardAnswer.objects.filter(is_visible=True)
    pagination_class = HALPagination


class FeedbackViewSet(
    viewsets.GenericViewSet, mixins.UpdateModelMixin, mixins.RetrieveModelMixin):
    """View to receive complaint/client feedback."""
    serializer_class = FeedbackSerializer
    queryset = Feedback.objects.all()

    def _raise_if_too_late_or_filled_out(self):
        """Raise HTTP 410 if feedback sent too late or twice or more."""
        obj = self.get_object()

        if timezone.now() > obj.requested_before:
            raise Gone(detail='too late')

        if obj.is_satisfied is not None:
            raise Gone(detail='filled out')

    def retrieve(self, request, *args, **kwargs):
        """Check whether feedback can still be submitted."""
        self._raise_if_too_late_or_filled_out()
    
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Submit feedback."""
        self._raise_if_too_late_or_filled_out()

        return super().update(request, *args, **kwargs)
