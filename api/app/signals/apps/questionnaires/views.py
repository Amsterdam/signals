# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import uuid

from datapunt_api.rest import DatapuntViewSet, DatapuntViewSetWritable
from django.utils import timezone
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import get_object_or_404

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.questionnaires.exceptions import Gone
from signals.apps.questionnaires.models import Question, Questionnaire, Session
from signals.apps.questionnaires.rest import HALViewSetRetrieve
from signals.apps.questionnaires.serializers import (
    PrivateQuestionDetailedSerializer,
    PrivateQuestionnaireDetailedSerializer,
    PrivateQuestionnaireSerializer,
    PrivateQuestionSerializer,
    PublicQuestionDetailedSerializer,
    PublicQuestionnaireDetailedSerializer,
    PublicQuestionnaireSerializer,
    PublicQuestionSerializer,
    PublicSessionDetailedSerializer,
    PublicSessionSerializer
)
from signals.auth.backend import JWTAuthBackend


class PublicQuestionnaireViewSet(DatapuntViewSet):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Questionnaire.objects.all()
    queryset_detail = Questionnaire.objects.all()

    serializer_class = PublicQuestionnaireSerializer
    serializer_detail_class = PublicQuestionnaireDetailedSerializer

    authentication_classes = ()


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
        elif (obj.created_at + timezone.timedelta(seconds=obj.ttl_seconds)) < now:
            raise Gone('Expired!')

        return obj
