# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from signals.apps.questionnaires.exceptions import SessionExpired, SessionFrozen
from signals.apps.questionnaires.models import Question, Session
from signals.apps.questionnaires.rest_framework.exceptions import Gone
from signals.apps.questionnaires.rest_framework.serializers.public.attachment import (
    PublicAttachmentSerializer
)
from signals.apps.questionnaires.rest_framework.serializers.public.sessions import (
    PublicSessionAnswerSerializer,
    PublicSessionSerializer
)
from signals.apps.questionnaires.rest_framework.utils import get_session_service_or_404
from signals.apps.questionnaires.rest_framework.viewsets import HALViewSetRetrieve


class PublicSessionViewSet(HALViewSetRetrieve):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Session.objects.none()

    serializer_class = PublicSessionSerializer
    serializer_detail_class = PublicSessionSerializer

    authentication_classes = ()

    def get_session_service(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
        )

        return get_session_service_or_404(self.kwargs[lookup_url_kwarg])

    def get_object(self, session_service=None):
        session_service = session_service or self.get_session_service()
        try:
            session_service.is_publicly_accessible()
        except (SessionFrozen, SessionExpired) as e:
            raise Gone(str(e))
        except Exception as e:
            raise APIException(str(e))  # For now just re-raise the exception as a DRF APIException
        else:
            return session_service.session

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context()
        context.update(kwargs)
        return context

    def retrieve(self, request, *args, **kwargs):
        session_service = self.get_session_service()
        session = self.get_object(session_service=session_service)
        serializer = self.get_serializer(session, context=self.get_serializer_context(session_service=session_service))
        return Response(serializer.data, status=200)

    @action(detail=True, url_path=r'submit/?$', methods=['POST', ])
    def submit(self, request, *args, **kwargs):
        # TODO: calls to this endpoint are not idempotent, investigate whether they should be.
        session_service = self.get_session_service()
        session = self.get_object(session_service)
        session_service.freeze()

        serializer = self.get_serializer(session, context=self.get_serializer_context(session_service=session_service))
        return Response(serializer.data, status=200)

    @action(detail=True, url_path=r'answers/?$', methods=['POST', ])
    def answers(self, request, *args, **kwargs):
        # TODO: finish / test
        session = self.get_object()
        session_service = get_session_service_or_404(session)

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

    @action(detail=True, url_path=r'attachments/?$', methods=['POST', ], serializer_class=PublicAttachmentSerializer,
            serializer_detail_class=PublicAttachmentSerializer)
    def attachments(self, request, *args, **kwargs):
        """
        Upload attachments for a specific session/question. The attachment will be validated and stored in the
        default_storage. The original name and location of the attachment will be stored in the payload of the answer.
        """
        session_service = get_session_service_or_404(self.get_object())
        context = self.get_serializer_context(session_service=session_service)

        serializer = self.serializer_class(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        serializer = PublicSessionSerializer(session_service.session, context=context)
        return Response(serializer.data, status=201)
