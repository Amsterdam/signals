# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.rest import DatapuntViewSetWritable
from rest_framework.exceptions import MethodNotAllowed

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.questionnaires.models import Question, Questionnaire
from signals.apps.questionnaires.rest_framework.serializers import (
    PrivateQuestionDetailedSerializer,
    PrivateQuestionnaireDetailedSerializer,
    PrivateQuestionnaireSerializer,
    PrivateQuestionSerializer
)
from signals.auth.backend import JWTAuthBackend


class PrivateQuestionnaireViewSet(DatapuntViewSetWritable):
    queryset = Questionnaire.objects.all()
    queryset_detail = Questionnaire.objects.all()

    serializer_class = PrivateQuestionnaireSerializer
    serializer_detail_class = PrivateQuestionnaireDetailedSerializer

    authentication_classes = (JWTAuthBackend, )
    permission_classes = (SIAPermissions, )

    def create(self, request, *args, **kwargs):
        # Not yet implemented
        raise MethodNotAllowed('Method not allowed!')

    def update(self, request, *args, **kwargs):
        # Not yet implemented
        raise MethodNotAllowed('Method not allowed!')

    def destroy(self, request, *args, **kwargs):
        # Not yet implemented
        raise MethodNotAllowed('Method not allowed!')


class PrivateQuestionViewSet(DatapuntViewSetWritable):
    queryset = Question.objects.all()
    queryset_detail = Question.objects.all()

    serializer_class = PrivateQuestionSerializer
    serializer_detail_class = PrivateQuestionDetailedSerializer

    authentication_classes = (JWTAuthBackend, )
    permission_classes = (SIAPermissions, )

    def create(self, request, *args, **kwargs):
        # Not yet implemented
        raise MethodNotAllowed('Method not allowed!')

    def update(self, request, *args, **kwargs):
        # Not yet implemented
        raise MethodNotAllowed('Method not allowed!')

    def destroy(self, request, *args, **kwargs):
        # Not yet implemented
        raise MethodNotAllowed('Method not allowed!')
