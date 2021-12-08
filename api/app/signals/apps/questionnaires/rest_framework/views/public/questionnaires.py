# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.rest import DatapuntViewSet

from signals.apps.questionnaires.models import Questionnaire
from signals.apps.questionnaires.rest_framework.serializers import (
    PublicQuestionnaireDetailedSerializer,
    PublicQuestionnaireSerializer
)


class PublicQuestionnaireViewSet(DatapuntViewSet):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Questionnaire.objects.active()
    queryset_detail = Questionnaire.objects.active()

    serializer_class = PublicQuestionnaireSerializer
    serializer_detail_class = PublicQuestionnaireDetailedSerializer

    authentication_classes = ()
