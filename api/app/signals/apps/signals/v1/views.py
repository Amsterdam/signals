"""
Views that are used exclusively by the V1 API
"""
from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSet
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views.generic.detail import SingleObjectMixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.status import HTTP_202_ACCEPTED

from signals.apps.signals.models import History, MainCategory, Signal, SubCategory
from signals.apps.signals.pdf.views import PDFTemplateView
from signals.apps.signals.v1.serializers import (
    HistoryHalSerializer,
    MainCategoryHALSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList,
    SubCategoryHALSerializer
)
from signals.auth.backend import JWTAuthBackend


class MainCategoryViewSet(DatapuntViewSet):
    queryset = MainCategory.objects.all()
    serializer_detail_class = MainCategoryHALSerializer
    serializer_class = MainCategoryHALSerializer
    lookup_field = 'slug'


class SubCategoryViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
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


class PrivateSignalViewSet(DatapuntViewSet):
    """Viewset for `Signal` objects in V1 private API"""
    queryset = Signal.objects.all()
    serializer_class = PrivateSignalSerializerList
    serializer_detail_class = PrivateSignalSerializerDetail
    pagination_class = HALPagination
    authentication_classes = (JWTAuthBackend, )
    filter_backends = (DjangoFilterBackend, )

    @action(detail=True)
    def history(self, request, pk=None):
        """History endpoint filterable by action."""
        POSSIBLE_HISTORY_ENTRIES = [
            'UPDATE_STATUS',
            'UPDATE_PRIORITY',
            'UPDATE_CATEGORY_ASSIGNMENT',
            'CREATE_NOTE',
            'UPDATE_LOCATION',
        ]

        history_entries = History.objects.filter(_signal__id=pk)
        what = self.request.query_params.get('what', None)
        if what and what in POSSIBLE_HISTORY_ENTRIES:
            history_entries = history_entries.filter(what=what)

        serializer = HistoryHalSerializer(history_entries, many=True)
        return Response(serializer.data)

    # https://stackoverflow.com/questions/45564130/django-rest-framework-image-upload
    # note starting DRF 3.8, @detail_route and @list_route are replaced with action

    @action(detail=True, methods=['POST'])
    def image(self, request, pk=None):
        signal = Signal.objects.get(pk=pk)

        if signal.image:
            raise PermissionDenied("Melding is reeds van foto voorzien.")

        # Check upload is present and not too big image wise:
        image = request.data.get('image', None)
        if image:
            if image.size > 8388608:  # 8MB = 8*1024*1024
                raise ValidationError("Foto mag maximaal 8Mb groot zijn.")
        else:
            raise ValidationError("Foto is een verplicht veld.")

        signal.image = image
        signal.save()

        # TODO: Check what to do about the headers (see V0 API)
        return Response({}, status=HTTP_202_ACCEPTED)


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
