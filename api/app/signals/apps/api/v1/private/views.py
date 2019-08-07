"""
Views that are used exclusively by the V1 API
"""
from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSet
from django.utils import timezone
from django.views.generic.detail import SingleObjectMixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from signals.apps.api import mixins
from signals.apps.api.generics.filters import FieldMappingOrderingFilter
from signals.apps.api.generics.permissions import ModelWritePermissions, SIAPermissions
from signals.apps.api.pdf.views import PDFTemplateView
from signals.apps.api.v1.filters import SignalCategoryRemovedAfterFilter, SignalFilter
from signals.apps.api.v1.serializers import (
    HistoryHalSerializer,
    PrivateSignalAttachmentSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList,
    PrivateSplitSignalSerializer,
    SignalIdListSerializer,
    StateStatusMessageTemplateSerializer,
    StoredSignalFilterSerializer
)
from signals.apps.signals.models import (
    Attachment,
    Category,
    History,
    Signal,
    StatusMessageTemplate,
    StoredSignalFilter
)
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

    filter_backends = (DjangoFilterBackend, FieldMappingOrderingFilter, )
    filterset_class = SignalFilter

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
    )
    ordering_field_mappings = {
        'id': 'id',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
        'stadsdeel': 'location__stadsdeel',
        'sub_category': 'category_assignment__category__slug',
        'main_category': 'category_assignment__category__parent__slug',
        'status': 'status__state',
        'priority': 'priority__priority',
        'address': 'location__address_text',
    }

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
            images=self.object.attachments.filter(is_image=True),
            user=self.request.user,
        )


class SignalCategoryRemovedAfterViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = SignalIdListSerializer
    pagination_class = HALPagination

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = SignalCategoryRemovedAfterFilter

    queryset = Signal.objects.only('id').all()


class StatusMessageTemplatesViewSet(mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                                    viewsets.GenericViewSet):
    serializer_class = StateStatusMessageTemplateSerializer

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions & ModelWritePermissions,)
    pagination_class = None

    queryset = StatusMessageTemplate.objects.none()

    def get_object(self):
        if 'slug' in self.kwargs and 'sub_slug' in self.kwargs:
            kwargs = {'parent__slug': self.kwargs['slug'],
                      'slug': self.kwargs['sub_slug']}
        else:
            kwargs = {'slug': self.kwargs['slug']}

        obj = get_object_or_404(Category.objects.all(), **kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_serializer_context(self):
        context = super(StatusMessageTemplatesViewSet, self).get_serializer_context()
        context.update({'category': self.get_object()})
        return context

    def retrieve(self, request, *args, **kwargs):
        status_message_templates = self.get_object().status_message_templates.all()
        serializer = self.get_serializer(status_message_templates, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return self.retrieve(request, *args, **kwargs)


class StoredSignalFilterViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                                mixins.CreateModelMixin, mixins.UpdateModelMixin,
                                mixins.DestroyModelMixin, viewsets.GenericViewSet):
    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    pagination_class = HALPagination
    serializer_class = StoredSignalFilterSerializer

    def get_queryset(self):
        return StoredSignalFilter.objects.filter(created_by=self.request.user.username)
