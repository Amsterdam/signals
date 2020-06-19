from datapunt_api.rest import DatapuntViewSet, HALPagination
from rest_framework import status
from rest_framework.response import Response

from signals.apps.api.generics import mixins
from signals.apps.api.generics.permissions import ModelWritePermissions, SIAPermissions
from signals.apps.api.v1.serializers import (
    PrivateDepartmentSerializerDetail,
    PrivateDepartmentSerializerList
)
from signals.apps.signals.models import Department
from signals.auth.backend import JWTAuthBackend


class PrivateDepartmentViewSet(mixins.ListModelMixin,
                               mixins.RetrieveModelMixin,
                               mixins.CreateModelMixin,
                               mixins.UpdateModelMixin,
                               DatapuntViewSet):
    queryset = Department.objects.all()

    serializer_class = PrivateDepartmentSerializerList
    serializer_detail_class = PrivateDepartmentSerializerDetail

    pagination_class = HALPagination

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions & ModelWritePermissions, )

    ordering = ('-code', )

    def create(self, request, *args, **kwargs):
        # If we create a department we want to use the detail serializer
        serializer = self.serializer_detail_class(data=request.data,
                                                  context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
