# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.rest import DatapuntViewSet
from django.http import Http404
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from signals.apps.questionnaires.exceptions import SessionExpired, SessionFrozen
from signals.apps.questionnaires.models import Question, Questionnaire, Session
from signals.apps.questionnaires.rest_framework.exceptions import Gone
from signals.apps.questionnaires.rest_framework.serializers import (
    PublicAnswerSerializer,
    PublicQuestionDetailedSerializer,
    PublicQuestionnaireDetailedSerializer,
    PublicQuestionnaireSerializer,
    PublicQuestionSerializer,
    PublicSessionDetailedSerializer,
    PublicSessionSerializer
)
from signals.apps.questionnaires.rest_framework.viewsets import HALViewSetRetrieve
from signals.apps.questionnaires.services.utils import get_session_service


class PublicQuestionnaireViewSet(DatapuntViewSet):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Questionnaire.objects.active()
    queryset_detail = Questionnaire.objects.active()

    serializer_class = PublicQuestionnaireSerializer
    serializer_detail_class = PublicQuestionnaireDetailedSerializer

    authentication_classes = ()


class PublicQuestionViewSet(DatapuntViewSet):
    lookup_field = 'retrieval_key'
    lookup_url_kwarg = 'retrieval_key'

    queryset = Question.objects.all()
    queryset_detail = Question.objects.all()

    serializer_class = PublicQuestionSerializer
    serializer_detail_class = PublicQuestionDetailedSerializer

    authentication_classes = ()

    def get_object(self):
        """
        Copied from rest_framework/generics.py::GenericAPIView::get_object
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
        )

        try:
            question = Question.objects.get_by_reference(self.kwargs[lookup_url_kwarg])
        except Question.DoesNotExist:
            raise Http404

        # May raise a permission denied
        self.check_object_permissions(self.request, question)

        return question

    @action(detail=True, url_path=r'answer/?$', methods=['POST', ], serializer_class=PublicAnswerSerializer)
    def answer(self, request, *args, **kwargs):
        question = self.get_object()

        context = self.get_serializer_context()
        context.update({'question': question})

        serializer = PublicAnswerSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        next_question_data = None

        # TODO: consider removing the serialized next_question, that is not
        # currently used and superseded by the path_questions available through
        # the SessionService (subclass).
        answer = serializer.instance
        session_service = get_session_service(answer.session)
        session_service.refresh_from_db()
        next_question = session_service.get_next_question(question, answer)

        if next_question:
            context = self.get_serializer_context()
            context.update({'graph': serializer.instance.session.questionnaire.graph})

            question_serializer = PublicQuestionSerializer(next_question, context=context)
            next_question_data = question_serializer.data

        data = serializer.data
        data.update({'next_question': next_question_data})

        return Response(data, status=201)


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

        try:
            session_service = get_session_service(session_uuid)
        except Session.DoesNotExist:
            raise Http404

        try:
            session_service.is_publicly_accessible()
        except (SessionFrozen, SessionExpired) as e:
            raise Gone(str(e))
        except Exception as e:
            # For now just re-raise the exception as a DRF APIException
            raise APIException(str(e))

        return session_service.session

    @action(detail=True, url_path=r'submit/?$', methods=['POST', ])
    def submit(self, request, *args, **kwargs):
        # TODO: calls to this endpoint are not idempotent, investigate whether
        # they should be.
        session = self.get_object()
        session_service = get_session_service(session)  # TODO: error handling
        session_service.freeze()

        serializer = self.serializer_detail_class(session, context=self.get_serializer_context())
        return Response(serializer.data, status=200)
