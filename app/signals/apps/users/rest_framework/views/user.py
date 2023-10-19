# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from django.contrib.auth import get_user_model
from django.db.models.functions import Lower
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.viewsets import ModelViewSet
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.api.generics.pagination import HALPagination
from signals.apps.api.generics.permissions import SIAPermissions, SIAUserPermissions
from signals.apps.history.services import HistoryLogService
from signals.apps.users.rest_framework.filters import UserFilterSet, UserNameListFilterSet
from signals.apps.users.rest_framework.serializers import (
    UserDetailHALSerializer,
    UserListHALSerializer
)
from signals.apps.users.rest_framework.serializers.user import (
    PrivateUserHistoryHalSerializer,
    UserNameListSerializer
)
from signals.auth.backend import JWTAuthBackend

# Get the user model as defined in the settings, defaults to the auth User from Django
User = get_user_model()


@extend_schema_view(
    list=extend_schema(description='List all users'),
    retrieve=extend_schema(description='Retrieve a user', responses={HTTP_200_OK: UserDetailHALSerializer}),
    partial_update=extend_schema(description='Update a user', request=UserDetailHALSerializer,
                                 responses={HTTP_200_OK: UserDetailHALSerializer}),
)
class UserViewSet(DetailSerializerMixin, ModelViewSet):
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

    authentication_classes = [JWTAuthBackend]
    permission_classes = (SIAUserPermissions,)

    serializer_detail_class = UserDetailHALSerializer
    serializer_class = UserListHALSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = UserFilterSet

    # We only allow these methods
    http_method_names = ['get', 'post', 'patch', 'head', 'options', 'trace']

    @extend_schema(responses={HTTP_201_CREATED: UserDetailHALSerializer}, request=UserDetailHALSerializer,
                   description='Create a user')
    def create(self, request, *args, **kwargs):
        # If we create a user we want to use the detail serializer
        serializer = self.serializer_detail_class(data=request.data,
                                                  context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        """
        perform the update and also add it to the history log
        """
        instance = serializer.save()
        HistoryLogService.log_update(instance=instance, user=self.request.user)

    @extend_schema(responses={HTTP_200_OK: PrivateUserHistoryHalSerializer})
    @action(detail=True)
    def history(self, request, pk=None):
        """
        The change log of the selected User instance
        This is read-only!
        """
        user = self.get_object()
        serializer = PrivateUserHistoryHalSerializer(user.history_log, many=True)
        return Response(serializer.data)


class LoggedInUserView(RetrieveAPIView):
    """
    Detail for the currently logged in user
    """
    queryset = User.objects.none()

    authentication_classes = [JWTAuthBackend]
    permission_classes = (SIAPermissions,)

    serializer_class = UserDetailHALSerializer
    pagination_class = None

    def get_object(self):
        return self.request.user


class AutocompleteUsernameListView(ListAPIView):
    """
    Returns a list of usernames filtered by username
    The username filter needs to provide at least 3 characters or more
    """
    queryset = User.objects.all().order_by(Lower('username'))

    authentication_classes = [JWTAuthBackend]
    permission_classes = (SIAPermissions,)

    serializer_class = UserNameListSerializer
    pagination_class = HALPagination

    filter_backends = (DjangoFilterBackend,)
    filterset_class = UserNameListFilterSet
