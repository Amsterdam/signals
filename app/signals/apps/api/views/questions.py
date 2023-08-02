# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ReadOnlyModelViewSet

from signals.apps.api.filters import QuestionFilterSet
from signals.apps.api.serializers import PublicQuestionSerializerDetail
from signals.apps.signals.models import Question


class PublicQuestionViewSet(ReadOnlyModelViewSet):
    queryset = Question.objects.all()

    serializer_class = PublicQuestionSerializerDetail
    filter_backends = (DjangoFilterBackend,)
    filterset_class = QuestionFilterSet
