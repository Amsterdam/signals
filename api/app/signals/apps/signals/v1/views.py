"""
Views that are used exclusively by the V1 API
"""
from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSet
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic.detail import SingleObjectMixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.signals import permissions
from signals.apps.signals.api_generics.permissions import SIAPermissions
from signals.apps.signals.models import Attachment, History, MainCategory, Signal, SubCategory
from signals.apps.signals.pdf.views import PDFTemplateView
from signals.apps.signals.v1.filters import SignalFilter
from signals.apps.signals.v1.serializers import (
    HistoryHalSerializer,
    MainCategoryHALSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList,
    PublicSignalCreateSerializer,
    PublicSignalSerializerDetail,
    SignalAttachmentSerializer,
    SplitPrivateSignalSerializerDetail,
    SubCategoryHALSerializer
)
from signals.auth.backend import JWTAuthBackend

""" PUBLIC endpoints """


class PublicMainCategoryViewSet(DatapuntViewSet):
    queryset = MainCategory.objects.all()
    serializer_detail_class = MainCategoryHALSerializer
    serializer_class = MainCategoryHALSerializer
    lookup_field = 'slug'


class PublicSubCategoryViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategoryHALSerializer
    pagination_class = HALPagination

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset,
                                main_category__slug=self.kwargs['slug'],
                                slug=self.kwargs['sub_slug'])
        self.check_object_permissions(self.request, obj)
        return obj


class PublicSignalViewSet(mixins.CreateModelMixin,
                          DetailSerializerMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    queryset = Signal.objects.all()
    serializer_class = PublicSignalCreateSerializer
    serializer_detail_class = PublicSignalSerializerDetail
    lookup_field = 'signal_id'


class GeneratePdfView(LoginRequiredMixin, SingleObjectMixin, PDFTemplateView):
    object = None
    pk_url_kwarg = 'signal_id'
    queryset = Signal.objects.all()

    template_name = 'signals/pdf/print_signal.html'
    extra_context = {'now': timezone.datetime.now(), }

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        self.pdf_filename = 'SIA-{}.pdf'.format(self.object.pk)
        rd_coordinates = self.object.location.get_rd_coordinates()
        bbox = '{},{},{},{}'.format(
            rd_coordinates.x - 340.00,
            rd_coordinates.y - 125.00,
            rd_coordinates.x + 340.00,
            rd_coordinates.y + 125.00,
        )
        return super(GeneratePdfView, self).get_context_data(bbox=bbox)


class PublicSignalAttachmentsViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = SignalAttachmentSerializer
    is_public = True
    lookup_field = 'signal_id'
    lookup_url_kwarg = 'signal_id'
    queryset = Signal.objects.all()


""" PRIVATE endpoints """


class PrivateSignalViewSetBase:
    """ Contains the logic for providing access to all signals or only signals from certain
    categories.

    If user has SIA_BACKOFFICE permission, the user has access to all signals (besides whatever
    restrictions are placed on the user permissions with the Django REST permission_classes). If the
    user does not have the SIA_BACKOFFICE permission, we make sure the user only receives signals
    from categories she has access to.

    IMPORTANT! This class should always be the first parent of the inheriting class, because
    we want get_object from this class to be called, instead of some other instance.
    """
    @property
    def all_signals(self):
        return Signal.objects

    @property
    def signals_queryset(self):
        if self.request.user and self.request.user.has_perm('signals.' + permissions.SIA_BACKOFFICE):
            return self.all_signals.all()

        category_ids = []

        return self.all_signals.filter(category_assignment__sub_category__id__in=category_ids)

    def get_signal(self, **filter_kwargs):
        # First query on all signals (triggers a 404)
        self.all_signals.get(**filter_kwargs)

        # Then return signal or trigger 403 (querying on filtered queryset here)
        try:
            return self.signals_queryset.get(**filter_kwargs)
        except Signal.DoesNotExist:
            raise PermissionDenied()

    def get_object(self):
        """ Returns signal object based on lookup_field and lookup_url_kwarg (standard Django REST
        fields). Takes into account the permissions the user has on subcategories. """
        lookup_kwarg = self.lookup_url_kwarg if self.lookup_url_kwarg else self.lookup_field
        return self.get_signal(**{self.lookup_field: self.kwargs[lookup_kwarg]})

    def get_queryset(self):
        return self.signals_queryset


class PrivateSignalAttachmentsViewSet(PrivateSignalViewSetBase,  # First parent!
                                      PublicSignalAttachmentsViewSet, mixins.ListModelMixin):
    is_public = False
    pagination_class = None
    lookup_field = 'pk'
    lookup_url_kwarg = 'pk'
    permission_classes = (SIAPermissions,)

    def get_queryset(self):
        return Attachment.actions.get_attachments(self.get_object())


class PrivateSignalViewSet(PrivateSignalViewSetBase,  # First parent!
                           DatapuntViewSet,
                           mixins.CreateModelMixin,
                           mixins.UpdateModelMixin):
    """Viewset for `Signal` objects in V1 private API"""
    serializer_class = PrivateSignalSerializerList
    serializer_detail_class = PrivateSignalSerializerDetail
    pagination_class = HALPagination
    authentication_classes = (JWTAuthBackend,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = SignalFilter
    permission_classes = (SIAPermissions,)

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

    @action(detail=True, methods=['POST'],
            serializer_detail_class=SplitPrivateSignalSerializerDetail)
    def split(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(many=True, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response(serializer.data, status=HTTP_201_CREATED)
