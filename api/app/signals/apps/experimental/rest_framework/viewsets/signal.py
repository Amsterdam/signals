# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import logging

from datapunt_api.rest import HALPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from signals.apps.api.generics.filters import FieldMappingOrderingFilter
from signals.apps.experimental.models.signals_filter_view import SignalFilterView
from signals.apps.experimental.rest_framework.filters.signal import SignalFilterSet
from signals.apps.experimental.rest_framework.serializers.signal import PrivateSignalSerializerList
from signals.auth.backend import JWTAuthBackend

logger = logging.getLogger(__name__)


class PrivateSignalViewSet(ListModelMixin, GenericViewSet):
    authentication_classes = (JWTAuthBackend, )

    queryset = SignalFilterView.objects.select_related(
        'category_assignment',
    ).prefetch_related(
        'routing_assignment__departments',
    ).all()

    serializer_class = PrivateSignalSerializerList
    pagination_class = HALPagination

    filter_backends = (DjangoFilterBackend, FieldMappingOrderingFilter, )
    filterset_class = SignalFilterSet
    ordering = ('-created_at', )
    ordering_fields = (
        'id',
        'created_at',
        'updated_at',
        'stadsdeel',
        'sub_category',
        'main_category',
        'status',
        'priority',
        'address',
        'assigned_user_email',
    )
    ordering_field_mappings = {
        'id': 'id',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
        'stadsdeel': 'location_stadsdeel',
        'sub_category': 'child_category_slug',
        'main_category': 'parent_category_slug',
        'status': 'status_state',
        'priority': 'priority_priority',
        'address': 'location_address_text',
        'assigned_user_email': 'assigned_user_email',
    }

    def get_queryset(self):
        # filter_for_user will filter according to the services/domain/permissions/util.py
        # this is copied from api/views/signal.py::PrivateSignalViewSet to make sure the permissions are the same on
        # both endpoints
        qs = super().get_queryset()
        return qs.filter_for_user(user=self.request.user)
