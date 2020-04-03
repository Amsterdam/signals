from datapunt_api.rest import DatapuntViewSetWritable
from django.contrib.auth import get_user_model
from django.db.models.functions import Lower
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.users.v1.filters import UserFilterSet
from signals.apps.users.v1.serializers import UserDetailHALSerializer, UserListHALSerializer
from signals.apps.users.v1.serializers.user import PrivateUserHistoryHalSerializer
from signals.auth.backend import JWTAuthBackend

# Get the user model as defined in the settings, defaults to the auth User from Django
User = get_user_model()


class UserViewSet(DatapuntViewSetWritable):
    queryset = User.objects.select_related(
        'profile'
    ).prefetch_related(
        'groups',
    ).order_by(Lower('username'))

    queryset_detail = User.objects.select_related(
        'profile'
    ).prefetch_related(
        'user_permissions',
        'user_permissions__content_type',
        'groups',
        'groups__permissions',
        'groups__permissions__content_type',
        'profile__departments',
    ).order_by(Lower('username'))

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions & DjangoModelPermissions,)

    serializer_detail_class = UserDetailHALSerializer
    serializer_class = UserListHALSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = UserFilterSet

    # We only allow these methods
    http_method_names = ['get', 'post', 'patch', 'head', 'options', 'trace']

    def create(self, request, *args, **kwargs):
        # If we create a user we want to use the detail serializer
        serializer = self.serializer_detail_class(data=request.data,
                                                  context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def me(self, request):
        """
        Detail for the currently logged in user
        """
        serializer = self.serializer_detail_class(request.user,
                                                  context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True)
    def history(self, request, pk=None):
        """
        The change log of the selected User instance
        This is read-only!
        """
        user = self.get_object()
        serializer = PrivateUserHistoryHalSerializer(user.logs, many=True)
        return Response(serializer.data)
