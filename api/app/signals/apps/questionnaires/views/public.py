# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import uuid

from datapunt_api.rest import DatapuntViewSet
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from signals.apps.questionnaires.models import Question, Questionnaire, Session
from signals.apps.questionnaires.rest_framework.exceptions import Gone
from signals.apps.questionnaires.rest_framework.viewsets import HALViewSetRetrieve
from signals.apps.questionnaires.serializers import (
    PublicAnswerSerializer,
    PublicQuestionDetailedSerializer,
    PublicQuestionnaireDetailedSerializer,
    PublicQuestionnaireSerializer,
    PublicQuestionSerializer,
    PublicSessionDetailedSerializer,
    PublicSessionSerializer
)
from signals.apps.questionnaires.services import QuestionnairesService


class PublicQuestionnaireViewSet(DatapuntViewSet):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Questionnaire.objects.all()
    queryset_detail = Questionnaire.objects.all()

    serializer_class = PublicQuestionnaireSerializer
    serializer_detail_class = PublicQuestionnaireDetailedSerializer

    authentication_classes = ()


class PublicQuestionViewSet(DatapuntViewSet):
    lookup_field = 'key'
    lookup_url_kwarg = 'key'

    queryset = Question.objects.all()
    queryset_detail = Question.objects.all()

    serializer_class = PublicQuestionSerializer
    serializer_detail_class = PublicQuestionDetailedSerializer

    authentication_classes = ()

    def get_object(self):
        """
        Copied from rest_framework/generics.py::GenericAPIView::get_object

        Added additional check to see if the given key is a valid UUID
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}

        try:
            # Check if the given string is a UUID
            # if so use it to get the question based on it's UUID
            lookup = uuid.UUID(self.kwargs[lookup_url_kwarg])
            filter_kwargs = {'uuid': lookup}
        except ValueError:
            pass

        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    @action(detail=True, url_path=r'answer/?$', methods=['POST', ], serializer_class=PublicAnswerSerializer)
    def answer(self, request, *args, **kwargs):
        question = self.get_object()

        context = self.get_serializer_context()
        context.update({'question': question})

        serializer = PublicAnswerSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        next_question_data = None
        next_question = QuestionnairesService.get_next_question(answer=serializer.instance, question=question)
        if next_question:
            question_serializer = PublicQuestionSerializer(next_question, context=self.get_serializer_context())
            next_question_data = question_serializer.data

        data = serializer.data
        data.update({'next_question': next_question_data})

        return Response(data, status=201)


class PublicSessionViewSet(HALViewSetRetrieve):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Session.objects.all()
    queryset_detail = Session.objects.all()

    serializer_class = PublicSessionSerializer
    serializer_detail_class = PublicSessionDetailedSerializer

    authentication_classes = ()

    def get_object(self):
        obj = super(PublicSessionViewSet, self).get_object()

        now = timezone.now()
        if obj.submit_before and obj.submit_before < now:
            raise Gone('Expired!')
        elif obj.created_at + obj.duration < now:
            raise Gone('Expired!')

        return obj
