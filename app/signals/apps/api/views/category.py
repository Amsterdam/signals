# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from django.utils import timezone
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.mixins import DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.status import HTTP_200_OK
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet
from rest_framework_extensions.mixins import DetailSerializerMixin, NestedViewSetMixin

from signals.apps.api.generics.permissions import ModelWritePermissions, SIAPermissions
from signals.apps.api.serializers import (
    CategoryHALSerializer,
    ParentCategoryHALSerializer,
    PrivateCategorySerializer
)
from signals.apps.api.serializers.category import (
    PrivateCategoryHistoryHalSerializer,
    PrivateCategoryIconSerializer
)
from signals.apps.history.models import Log
from signals.apps.history.services import HistoryLogService
from signals.apps.signals.models import Category
from signals.auth.backend import JWTAuthBackend


@extend_schema_view(
    list=extend_schema(
        responses=PolymorphicProxySerializer(
            component_name='Category',
            serializers=[ParentCategoryHALSerializer, CategoryHALSerializer, ],
            resource_type_field_name='sub_categories',
            many=True
        )
    ),
    retrieve=extend_schema(
        responses=PolymorphicProxySerializer(
            component_name='Category',
            serializers=[ParentCategoryHALSerializer, CategoryHALSerializer, ],
            resource_type_field_name='sub_categories',
            many=False
        )
    )
)
class PublicCategoryViewSet(NestedViewSetMixin, DetailSerializerMixin, ReadOnlyModelViewSet):
    queryset = Category.objects.select_related('parent').prefetch_related('children').all()
    lookup_field = 'slug'

    def get_queryset(self):
        if self.get_parents_query_dict():
            return super().get_queryset()
        return self.queryset.filter(parent__isnull=True)

    def get_serializer(self, *args, **kwargs):
        if self.get_parents_query_dict():
            serializer_class = CategoryHALSerializer
        else:
            serializer_class = ParentCategoryHALSerializer

        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)


class PrivateCategoryViewSet(UpdateModelMixin, DetailSerializerMixin, ReadOnlyModelViewSet):
    serializer_class = PrivateCategorySerializer
    serializer_detail_class = PrivateCategorySerializer

    queryset = Category.objects.prefetch_related(
        'slo',
        'categorydepartment_set',
        'categorydepartment_set__department',
    ).all()

    authentication_classes = [JWTAuthBackend]
    permission_classes = (SIAPermissions & ModelWritePermissions,)

    def perform_update(self, serializer):
        """
        perform the update and also add it to the history log
        """
        instance = serializer.save()
        HistoryLogService.log_update(instance=instance, user=self.request.user)

    @extend_schema(
        responses={
            HTTP_200_OK: PrivateCategoryHistoryHalSerializer(many=True),
        }
    )
    @action(detail=True, url_path='history', pagination_class=None)
    def history(self, request, pk=None):
        """
        The change log of the selected Category instance
        This is read-only!
        """
        category = self.get_object()
        serializer = PrivateCategoryHistoryHalSerializer(category.history_log.all(), many=True)
        return Response(serializer.data)


@extend_schema_view(
    update=extend_schema(
        request={
            'multipart/form-data': PrivateCategoryIconSerializer
        }
    )
)
class PrivateCategoryIconViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    lookup_url_kwarg = 'category_id'
    queryset = Category.objects.all()
    authentication_classes = [JWTAuthBackend]
    permission_classes = (SIAPermissions & ModelWritePermissions, )
    serializer_class = PrivateCategoryIconSerializer

    def perform_update(self, serializer: BaseSerializer) -> None:
        instance = serializer.save()
        HistoryLogService.log_update(instance=instance, user=self.request.user)

    def perform_destroy(self, instance: Category) -> None:
        instance.icon.delete()
        instance.history_log.create(
            action=Log.ACTION_UPDATE,
            created_by=self.request.user.username,
            created_at=timezone.now(),
            data={'icon': ''}
        )
