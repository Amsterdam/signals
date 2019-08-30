from datapunt_api.rest import DatapuntViewSet, HALPagination

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.reporting.models import ReportDefinition
from signals.apps.reporting.serializers import PrivateReportSerializer
from signals.auth.backend import JWTAuthBackend

from rest_framework.response import Response
from rest_framework.decorators import action


class ReportViewSet(DatapuntViewSet):
    serializer_class = PrivateReportSerializer
    serializer_detail_class = PrivateReportSerializer

    pagination_class = HALPagination

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)
    # TODO: add new permission for reports, use it here.

    queryset = ReportDefinition.objects.all()

    @action(detail=True)
    def data(self, request, pk=None):
        report_definition = ReportDefinition.objects.get(pk=pk)
        # TODO: add proper handling of repeated query parameters (probably
        # produce an HTTP 400 bad request).
        parameters = {
            'isoyear': request.query_params.get('isoyear', None),
            'isoweek': request.query_params.get('isoweek', None),
            'year': request.query_params.get('year', None),
            'month': request.query_params.get('month', None),
        }
        data = report_definition.derive(**parameters)

        return Response(data)
