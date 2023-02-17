# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from datapunt_api.rest import DatapuntViewSet, HALPagination
from django_filters.rest_framework import DjangoFilterBackend

from signals.apps.api.filters import QuestionFilterSet
from signals.apps.api.serializers import PublicQuestionSerializerDetail
from signals.apps.signals.models import Question


class PublicQuestionViewSet(DatapuntViewSet):
    queryset = Question.objects.all()

    serializer_class = PublicQuestionSerializerDetail
    serializer_detail_class = PublicQuestionSerializerDetail
    pagination_class = HALPagination
    filter_backends = (DjangoFilterBackend, )
    filterset_class = QuestionFilterSet
