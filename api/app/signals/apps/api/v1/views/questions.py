from datapunt_api.rest import DatapuntViewSet, HALPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response

from signals.apps.api.generics import mixins
from signals.apps.api.v1.filters import QuestionFilterSet
from signals.apps.api.v1.serializers import (
    PrivateQuestionSerializerDetail,
    PublicQuestionSerializerDetail
)
from signals.apps.signals.models import Question
from signals.auth.backend import JWTAuthBackend


class _BaseQuestionViewSet(DatapuntViewSet):
    queryset = Question.objects.all()
    pagination_class = HALPagination
    filter_backends = (DjangoFilterBackend, )


class PublicQuestionViewSet(_BaseQuestionViewSet):
    http_method_names = ['get']
    serializer_class = PublicQuestionSerializerDetail
    serializer_detail_class = PublicQuestionSerializerDetail
    filterset_class = QuestionFilterSet


class PrivateQuestionViewSet(mixins.ListModelMixin,
                             mixins.CreateModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.DestroyModelMixin,
                             _BaseQuestionViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    authentication_classes = (JWTAuthBackend,)
    serializer_class = PrivateQuestionSerializerDetail
    serializer_detail_class = PrivateQuestionSerializerDetail

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_detail_class(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
