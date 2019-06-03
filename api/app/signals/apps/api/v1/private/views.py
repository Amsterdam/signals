"""
Views that are used exclusively by the V1 API
"""
from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSet
from django.core.exceptions import ValidationError as CoreValidationError
from django.utils import timezone
from django.views.generic.detail import SingleObjectMixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from signals.apps.api import mixins
from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.pdf.views import PDFTemplateView
from signals.apps.api.v1.filters import SignalCategoryRemovedAfterFilter, SignalFilter
from signals.apps.api.v1.serializers import (
    HistoryHalSerializer,
    PrivateSignalAttachmentSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList,
    PrivateSplitSignalSerializer,
    SignalIdListSerializer,
    StatusMessageTemplateSerializer
)
from signals.apps.signals.models import Attachment, History, Signal, StatusMessageTemplate
from signals.auth.backend import JWTAuthBackend


class PrivateSignalViewSet(DatapuntViewSet,
                           mixins.CreateModelMixin,
                           mixins.UpdateModelMixin):
    """Viewset for `Signal` objects in V1 private API"""
    queryset = Signal.objects.select_related(
        'location',
        'status',
        'category_assignment',
        'category_assignment__category__parent',
        'reporter',
        'priority',
        'parent',
    ).prefetch_related(
        'category_assignment__category__departments',
        'children',
        'attachments',
        'notes',
    ).all()

    serializer_class = PrivateSignalSerializerList
    serializer_detail_class = PrivateSignalSerializerDetail

    pagination_class = HALPagination

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = SignalFilter

    http_method_names = ['get', 'post', 'patch', 'head', 'options', 'trace']

    @action(detail=True)
    def history(self, request, pk=None):
        """History endpoint filterable by action."""
        history_entries = History.objects.filter(_signal__id=pk)
        what = self.request.query_params.get('what', None)
        if what:
            history_entries = history_entries.filter(what=what)

        serializer = HistoryHalSerializer(history_entries, many=True)
        return Response(serializer.data)


class PrivateSignalSplitViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    serializer_class = PrivateSplitSignalSerializer
    queryset = Signal.objects.all()
    pagination_class = None

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)


class PrivateSignalAttachmentsViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                                      viewsets.GenericViewSet):
    serializer_class = PrivateSignalAttachmentSerializer
    pagination_class = HALPagination
    queryset = Attachment.objects.all()

    lookup_url_kwarg = 'pk'

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    def _filter_kwargs(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
        )

        return {self.lookup_field: self.kwargs[lookup_url_kwarg]}

    def get_object(self):
        self.lookup_field = self.lookup_url_kwarg

        obj = get_object_or_404(Signal.objects.all(), **self._filter_kwargs())
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        self.lookup_field = '_signal_id'

        qs = super(PrivateSignalAttachmentsViewSet, self).get_queryset()
        return qs.filter(**self._filter_kwargs())


class GeneratePdfView(SingleObjectMixin, PDFTemplateView):
    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)
    pagination_class = None

    queryset = Signal.objects.all()

    template_name = 'api/pdf/print_signal.html'
    extra_context = {'now': timezone.datetime.now(), }

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        rd_coordinates = self.object.location.get_rd_coordinates()
        bbox = '{},{},{},{}'.format(
            rd_coordinates.x - 340.00,
            rd_coordinates.y - 125.00,
            rd_coordinates.x + 340.00,
            rd_coordinates.y + 125.00,
        )
        return super(GeneratePdfView, self).get_context_data(
            bbox=bbox,
            images=self.object.attachments.filter(is_image=True)
        )


class SignalCategoryRemovedAfterViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = SignalIdListSerializer
    pagination_class = HALPagination

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = SignalCategoryRemovedAfterFilter

    queryset = Signal.objects.only('id').all()


class StoreStatusMessageTemplates(viewsets.GenericViewSet, mixins.CreateModelMixin,
                                  mixins.DestroyModelMixin, mixins.UpdateModelMixin):
    serializer_class = StatusMessageTemplateSerializer
    serializer_detail_class = StatusMessageTemplateSerializer

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)
    pagination_class = None

    queryset = StatusMessageTemplate.objects.all()

    def create(self, request, *args, **kwargs):
        many = type(request.data) in [list, tuple]

        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)
        except CoreValidationError as e:
            raise ValidationError(e.message)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instances = []
        for data in self.request.data:
            self.kwargs['pk'] = data['pk']
            instance = self.get_object()

            serializer = self.get_serializer(instance, data=data, partial=partial, many=False)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}
            instances.append(instance)

        serializer = self.get_serializer(instances, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        self.get_queryset().filter(pk__in=[data['pk'] for data in request.data]).delete()
        return Response(status=HTTP_204_NO_CONTENT)
