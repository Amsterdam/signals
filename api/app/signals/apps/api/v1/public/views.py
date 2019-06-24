import json
from urllib.parse import urlparse

import requests
from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSet
from django.conf import settings
from django.http import Http404
from django.urls import resolve
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.api.v1.serializers import (
    CategoryHALSerializer,
    ParentCategoryHALSerializer,
    PublicSignalAttachmentSerializer,
    PublicSignalCreateSerializer,
    PublicSignalSerializerDetail
)
from signals.apps.signals.models import Category, Signal
from signals.apps.signals.models.category_translation import CategoryTranslation


class PublicSignalGenericViewSet(GenericViewSet):
    lookup_field = 'signal_id'
    lookup_url_kwarg = 'signal_id'

    queryset = Signal.objects.all()

    pagination_class = None


class PublicSignalViewSet(CreateModelMixin, DetailSerializerMixin, RetrieveModelMixin,
                          PublicSignalGenericViewSet):
    serializer_class = PublicSignalCreateSerializer
    serializer_detail_class = PublicSignalSerializerDetail


class PublicSignalAttachmentsViewSet(CreateModelMixin, PublicSignalGenericViewSet):
    serializer_class = PublicSignalAttachmentSerializer


class ParentCategoryViewSet(DatapuntViewSet):
    queryset = Category.objects.filter(parent__isnull=True)
    serializer_detail_class = ParentCategoryHALSerializer
    serializer_class = ParentCategoryHALSerializer
    lookup_field = 'slug'


class ChildCategoryViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoryHALSerializer
    pagination_class = HALPagination

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        if 'slug' in self.kwargs and 'sub_slug' in self.kwargs:
            obj = get_object_or_404(queryset,
                                    parent__slug=self.kwargs['slug'],
                                    slug=self.kwargs['sub_slug'])
        else:
            obj = get_object_or_404(queryset, slug=self.kwargs['slug'])

        self.check_object_permissions(self.request, obj)
        return obj


class NamespaceView(APIView):
    """
    Used for the curies namespace, at this moment it is just a dummy landing page so that we have
    a valid URI that resolves

    TODO: Implement HAL standard for curies in the future
    """

    def get(self, request):
        return Response()


class MLPredictCategoryView(RetrieveModelMixin, GenericViewSet):
    queryset = Category.objects.none()
    serializer_class = CategoryHALSerializer
    pagination_class = None
    endpoint = '{}/predict'.format(settings.ML_TOOL_ENDPOINT)

    def _ml_predict(self):
        if 'text' not in self.request.data:
            raise ValidationError('Invalid request')
        text = self.request.data['text']

        response = requests.post(self.endpoint, data=json.dumps({'text': text}))
        if response.status_code == 200:
            return response.json()['subrubriek'][0][0]
        elif 500 <= response.status_code < 600:
            raise APIException
        else:
            raise Http404

    def get_object(self):
        prediction = self._ml_predict()
        slug = resolve(urlparse(prediction).path).kwargs['sub_slug'] if prediction else 'overig'

        try:
            # check if we need to translate the prediction by the ML tool
            translation = CategoryTranslation.objects.get(old_category__slug=slug)
            obj = translation.new_category
        except CategoryTranslation.DoesNotExist:
            obj = get_object_or_404(Category, slug=slug, is_active=True, parent__isnull=False)

        self.check_object_permissions(self.request, obj)
        return obj
