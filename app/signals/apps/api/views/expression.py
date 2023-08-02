# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import time

from django.contrib.gis import geos
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from signals.apps.api.filters.expression import ExpressionFilterSet
from signals.apps.api.generics.permissions import ModelWritePermissions, SIAPermissions
from signals.apps.api.serializers.expression import (
    ExpressionContextSerializer,
    ExpressionSerializer
)
from signals.apps.services.domain.dsl import DslService
from signals.apps.signals.models import Expression, ExpressionContext
from signals.auth.backend import JWTAuthBackend


class PrivateExpressionViewSet(ModelViewSet):
    """
    private ViewSet to display/process expressions in the database
    """
    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions & ModelWritePermissions,)

    queryset = Expression.objects.all()

    filter_backends = (DjangoFilterBackend,)
    filterset_class = ExpressionFilterSet

    serializer_class = ExpressionSerializer

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

    @extend_schema(
        parameters=[
            OpenApiParameter(name='type', location=OpenApiParameter.QUERY,
                             description='The expression type', required=True, type=str),
            OpenApiParameter(name='expression', location=OpenApiParameter.QUERY,
                             description='The expression to validate', required=True, type=str),
        ],
    )
    @action(detail=False, url_path='validate')
    def validate(self, request: Request) -> Response:
        """Validate expression for a certain expression type"""
        exp_type = request.query_params.get('type', False)
        exp = request.query_params.get('expression', False)
        if not exp or not exp_type:
            raise ValidationError({'result': 'type and expression required'})

        # populate context based on exp_type
        ctx = {
            t.identifier: self._default_context_type.get(t.identifier_type, None)
            for t in ExpressionContext.objects.filter(_type__name=exp_type)
        }

        result = self.dsl_service.validate(ctx, exp)
        if result:
            raise ValidationError({'result': result})
        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='type', location=OpenApiParameter.QUERY,
                             description='The expression type', required=True, type=str),
        ],
    )
    @action(detail=False, url_path='context')
    def context(self, request: Request) -> Response:
        """Returns available identifers for expression type"""
        exp_type = request.query_params.get('type', False)
        if not exp_type:
            raise ValidationError({'result': 'type required'})

        ctx = ExpressionContext.objects.filter(_type__name=exp_type)
        serializer = ExpressionContextSerializer(ctx, many=True)
        return Response(serializer.data)
