import time

from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSetWritable
from django.contrib.gis import geos
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from signals.apps.api.generics.permissions import ModelWritePermissions, SIAPermissions
from signals.apps.api.v1.filters.expression import ExpressionFilterSet
from signals.apps.api.v1.serializers.expression import (
    ExpressionContextSerializer,
    ExpressionSerializer
)
from signals.apps.services.domain.dsl import DslService
from signals.apps.signals.models import Expression, ExpressionContext
from signals.auth.backend import JWTAuthBackend


class PrivateExpressionViewSet(DatapuntViewSetWritable):
    """
    V1 private ViewSet to display/process expressions in the database
    """

    authentication_classes = (JWTAuthBackend, )
    queryset = Expression.objects.all()
    queryset_detail = Expression.objects.all()

    serializer_class = ExpressionSerializer
    serializer_detail_class = ExpressionSerializer

    pagination_class = HALPagination

    filter_backends = (DjangoFilterBackend, )
    permission_classes = (SIAPermissions & ModelWritePermissions, )

    filterset_class = ExpressionFilterSet

    dsl_service = DslService()

    # default values for certain types. is used by validator to validate expressions
    _default_context_type = {
        ExpressionContext.CTX_DICT: dict(),
        ExpressionContext.CTX_NUMBER: 1,
        ExpressionContext.CTX_POINT: geos.Point(1, 1),
        ExpressionContext.CTX_SET: set(),
        ExpressionContext.CTX_STRING: 'dummy',
        ExpressionContext.CTX_TIME: time.strptime("12:00:00", "%H:%M:%S")
    }

    def _result_msg(self, msg):
        return {
            'result': msg
        }

    def _bad_request(self, msg):
        return Response(
            data=self._result_msg(msg),
            status=status.HTTP_400_BAD_REQUEST
        )

    def _context_from_type(self, exp_type):
        return {
            t.identifier: self._default_context_type.get(t.identifier_type, None)
            for t in ExpressionContext.objects.filter(_type__name=exp_type)
        }

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_detail_class(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, url_path='validate/')
    def validate(self, request):
        """Validate expression for a certain expression type"""
        exp_type = request.query_params.get('type', None)
        exp = request.query_params.get('expression', None)
        if not exp or not exp_type:
            return self._bad_request('type and expression required')
        # populate context based on exp_type
        ctx = self._context_from_type(exp_type)
        result = self.dsl_service.validate(ctx, exp)
        if not result:
            return Response(status=status.HTTP_200_OK)
        else:
            return self._bad_request(result)

    @action(detail=False, url_path='context/')
    def context(self, request):
        """Returns available identifers for expression type"""
        exp_type = request.query_params.get('type', None)
        if not exp_type:
            return self._bad_request('type required')

        ctx = ExpressionContext.objects.filter(_type__name=exp_type)

        serializer = ExpressionContextSerializer(ctx, many=True)
        return Response(serializer.data)
