# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from datapunt_api.rest import DisplayField, HALSerializer

from signals.apps.questionnaires.models import Questionnaire
from signals.apps.questionnaires.rest_framework.fields import QuestionnairePublicLinksField
from signals.apps.questionnaires.rest_framework.serializers.public.illustrated_text import (
    NestedPublicIllustratedTextSerializer
)
from signals.apps.questionnaires.rest_framework.serializers.public.questions import (
    PublicQuestionDetailedSerializer,
    PublicQuestionSerializer
)


class PublicQuestionnaireSerializer(HALSerializer):
    serializer_url_field = QuestionnairePublicLinksField

    _display: DisplayField = DisplayField()
    first_question = PublicQuestionSerializer()
    explanation = NestedPublicIllustratedTextSerializer()

    class Meta:
        model = Questionnaire
        fields = (
            '_links',
            '_display',
            'uuid',
            'name',
            'description',
            'is_active',
            'first_question',
            'explanation',
        )
        read_only_fields = fields  # No create or update allowed


class PublicQuestionnaireDetailedSerializer(PublicQuestionnaireSerializer):
    first_question = PublicQuestionDetailedSerializer()
