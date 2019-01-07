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

from signals.apps.signals.models import (
    CategoryAssignment,
    History,
    Location,
    MainCategory,
    Note,
    Priority,
    Signal,
    Status,
    SubCategory,
)
from signals.apps.signals.pdf.views import PDFTemplateView
from signals.apps.signals.v1.serializers import (
    CategoryHALSerializer,
    HistoryHalSerializer,
    LocationHALSerializer,
    MainCategoryHALSerializer,
    NoteHALSerializer,
    PriorityHALSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList,
    StatusHALSerializer,
    SubCategoryHALSerializer,
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

    @action(detail=True)  # default GET gets routed here
    def history(self, request, pk=None):
        history_entries = History.objects.filter(_signal__id=pk)
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

    # Speculative (subject to business approval) - only serialize the current
    # information on the detail view of a `signal` instance, on paths below that
    # show the various update histories - leads to smaller JSON on the detail
    # view page. This is a slight deviation from the original V1 design.
    @action(detail=True, methods=['GET'])
    def statusses(self, request, pk=None):  # required for compat. with V0
        status_entries = Status.objects.filter(_signal__id=pk)
        serializer = StatusHALSerializer(status_entries, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def locations(self, request, pk=None):
        location_entries = Location.objects.filter(_signal__id=pk)
        serializer = LocationHALSerializer(location_entries, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def categories(self, request, pk=None):
        category_assignment_entries = CategoryAssignment.objects.filter(_signal__id=pk)
        serializer = CategoryHALSerializer(category_assignment_entries, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def priorities(self, request, pk=None):
        priority_entries = Priority.objects.filter(_signal__id=pk)
        serializer = PriorityHALSerializer(priority_entries, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def notes(self, request, pk=None):  # required for compat. with V0
        note_entries = Note.objects.filter(_signal__id=pk)
        serializer = NoteHALSerializer(note_entries, many=True)

        return Response(serializer.data)


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
