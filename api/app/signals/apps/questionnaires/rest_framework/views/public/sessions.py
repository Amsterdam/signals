# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from signals.apps.questionnaires.exceptions import SessionExpired, SessionFrozen
from signals.apps.questionnaires.models import Question, Session
from signals.apps.questionnaires.rest_framework.exceptions import Gone
from signals.apps.questionnaires.rest_framework.serializers.public.sessions import (
    PublicSessionAnswerSerializer,
    PublicSessionDetailedSerializer,
    PublicSessionSerializer
)
from signals.apps.questionnaires.rest_framework.views.utils import get_session_service_or_404
from signals.apps.questionnaires.rest_framework.viewsets import HALViewSetRetrieve
from signals.apps.questionnaires.services.utils import get_session_service


class PublicSessionViewSet(HALViewSetRetrieve):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Session.objects.none()
    queryset_detail = Session.objects.none()

    serializer_class = PublicSessionSerializer
    serializer_detail_class = PublicSessionDetailedSerializer

    authentication_classes = ()

    def get_object(self):
        session_uuid = self.kwargs[self.lookup_url_kwarg]
        session_service = get_session_service_or_404(session_uuid)

        try:
            session_service.is_publicly_accessible()
        except (SessionFrozen, SessionExpired) as e:
            raise Gone(str(e))
        except Exception as e:
            # For now just re-raise the exception as a DRF APIException
            raise APIException(str(e))

        return session_service.session

    def retrieve(self, request, *args, **kwargs):
        session = self.get_object()
        session_service = get_session_service(session)  # TODO: error handling

        context = self.get_serializer_context()
        context['session_service'] = session_service

        serializer = self.serializer_detail_class(session, context=context)
        return Response(serializer.data, status=200)

    @action(detail=True, url_path=r'submit/?$', methods=['POST', ])
    def submit(self, request, *args, **kwargs):
        # TODO: calls to this endpoint are not idempotent, investigate whether
        # they should be.
        session = self.get_object()
        session_service = get_session_service(session)  # TODO: error handling
        session_service.freeze()

        context = self.get_serializer_context()
        context['session_service'] = session_service

        serializer = self.serializer_detail_class(session, context=context)
        return Response(serializer.data, status=200)

    @action(detail=True, url_path=r'answers/?$', methods=['POST', ])
    def answers(self, request, *args, **kwargs):
        # TODO: finish / test
        session = self.get_object()
        session_service = get_session_service(session)

        # We demand an array of answers, even if only a single answer is present.
        serializer = PublicSessionAnswerSerializer(data=request.data, many=True)
        serializer.is_valid()

        answer_payloads = []
        questions = []

        retrieval_errors_by_uuid = []
        for answer_data in serializer.data:
            uuid = answer_data['question_uuid']
            assert isinstance(uuid, str)
            try:
                question = Question.objects.get_by_reference(uuid)
            except Question.DoesNotExist as e:
                # we silently ignore retrieval errors for now (UUIDs to non existant questions)
                retrieval_errors_by_uuid[answer_data[uuid]] = str(e)
                continue

            answer_payloads.append(answer_data['payload'])
            questions.append(question)

        session_service.create_answers(answer_payloads, questions)
        context = self.get_serializer_context()
        context['session_service'] = session_service  # session_service will have our validation errors

        serializer = self.serializer_detail_class(session, context=context)
        # TODO, consider status code - possibly return 400 if all answers were rejected
        return Response(serializer.data, status=200)
