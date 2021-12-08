# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.rest import DatapuntViewSet
from django.http import Http404
from rest_framework.decorators import action
from rest_framework.response import Response

from signals.apps.questionnaires.models import Question
from signals.apps.questionnaires.rest_framework.serializers import (
    PublicAnswerSerializer,
    PublicQuestionDetailedSerializer,
    PublicQuestionSerializer
)
from signals.apps.questionnaires.services.utils import get_session_service


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
