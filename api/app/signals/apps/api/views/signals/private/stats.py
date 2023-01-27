from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from signals.apps.signals.models.signal import Signal
from signals.apps.api.serializers.stats import TotalSerializer


class StatsViewSet(ViewSet):
    def total(self, request) -> Response:
        state = request.query_params.get('status')
        if state is None:
            return Response('No status parameter provided in querystring.', status=status.HTTP_400_BAD_REQUEST)

        queryset = Signal.objects.filter(status__state=state)

        category = request.query_params.get('category')
        if category is not None:
            queryset = queryset.filter(category_assignment__category__parent_id=category)

        serializer = TotalSerializer({'total': queryset.count()})

        return Response(serializer.data)
