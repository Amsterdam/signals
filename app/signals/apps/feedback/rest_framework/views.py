# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
"""
Views for feedback handling.
"""
from typing import Union

from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_410_GONE
from rest_framework.viewsets import GenericViewSet

from signals.apps.feedback.models import Feedback, StandardAnswer
from signals.apps.feedback.rest_framework.exceptions import Gone
from signals.apps.feedback.rest_framework.serializers import (
    FeedbackSerializer,
    StandardAnswerSerializer
)
from signals.schema import GenericErrorSerializer


class StandardAnswerViewSet(ListModelMixin, GenericViewSet):
    """View to list all currently visible Standard Answers."""
    serializer_class = StandardAnswerSerializer
    queryset = StandardAnswer.objects.select_related(
        'topic'
    ).filter(
        is_visible=True
    ).order_by(
        'topic__order',
        'order',
        '-id',
    )


@extend_schema_view(
    retrieve=extend_schema(responses={HTTP_200_OK: FeedbackSerializer,
                                      HTTP_404_NOT_FOUND: GenericErrorSerializer,
                                      HTTP_410_GONE: GenericErrorSerializer}),
    update=extend_schema(responses={HTTP_200_OK: FeedbackSerializer,
                                    HTTP_404_NOT_FOUND: GenericErrorSerializer,
                                    HTTP_410_GONE: GenericErrorSerializer}),
    partial_update=extend_schema(responses={HTTP_200_OK: FeedbackSerializer,
                                            HTTP_404_NOT_FOUND: GenericErrorSerializer,
                                            HTTP_410_GONE: GenericErrorSerializer}),
)
class FeedbackViewSet(UpdateModelMixin, RetrieveModelMixin, GenericViewSet):
    """View to receive complaint/client feedback."""
    serializer_class = FeedbackSerializer
    queryset = Feedback.objects.all()

    def get_object(self) -> Union[Feedback, Http404, Gone]:
        obj = super().get_object()

        if obj.is_too_late:
            raise Gone(detail='too late')

        if obj.is_filled_out:
            raise Gone(detail='filled out')

        return obj
