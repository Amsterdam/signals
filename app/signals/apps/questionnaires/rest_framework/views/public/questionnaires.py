# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from rest_framework.decorators import action
from rest_framework.response import Response

from signals.apps.questionnaires.models import Questionnaire, Session
from signals.apps.questionnaires.rest_framework.serializers.public.questionnaires import (
    PublicQuestionnaireDetailedSerializer,
    PublicQuestionnaireSerializer
)
from signals.apps.questionnaires.rest_framework.serializers.public.sessions import (
    PublicSessionSerializer
)
from signals.apps.questionnaires.rest_framework.utils import get_session_service_or_404
from signals.apps.questionnaires.rest_framework.viewsets import HALViewSetRetrieve


class PublicQuestionnaireViewSet(HALViewSetRetrieve):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Questionnaire.objects.active().order_by('-created_at')
    queryset_detail = Questionnaire.objects.active()

    serializer_class = PublicQuestionnaireSerializer
    serializer_detail_class = PublicQuestionnaireDetailedSerializer

    authentication_classes = ()

    @action(detail=True, url_path=r'session/?$', methods=['POST', ])
    def create_session(self, request, *args, **kwargs):
        # Create the Session instance for the selected Questionnaire
        session = Session.objects.create(questionnaire=self.get_object())

        # Return the Session
        session_service = get_session_service_or_404(session)
        context = self.get_serializer_context()
        context.update({'session_service': session_service})
        serializer = PublicSessionSerializer(session, context=context)
        return Response(serializer.data, status=201)
