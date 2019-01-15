from collections import defaultdict
from datetime import timedelta

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from signals.apps.signals import workflow
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend


class DashboardProtype(APIView):
    authentication_classes = (JWTAuthBackend, )

    def get(self, request, format=None):
        now = timezone.now()
        # Round up to next full hour, use that as end of report. If we are exactly at
        # the start of an hour, still move the end time to next hour.
        report_end = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        # Start of reporting is 24 hours earlier:
        report_start = report_end - timedelta(days=1)

        signals_last_24h = (
            Signal.objects.filter(created_at__gte=report_start)
                          .filter(created_at__lte=report_end)
                          .select_related('status')
                          .select_related('category_assignment')
        )

        r = signals_last_24h.values_list(
            'created_at',
            'status__state',
            'category_assignment__sub_category__main_category__name',
        )

        status_choices_mapping = {
            state: state_desc for state, state_desc in workflow.STATUS_CHOICES
        }

        status_counts = defaultdict(int)
        category_counts = defaultdict(int)

        for created_at, state, category in r:
            status_counts[status_choices_mapping[state]] += 1
            category_counts[category] += 1

        data = {
            'status': [{'name': k, 'count': v} for k, v in status_counts.items()],
            'category': [{'name': k, 'count': v} for k, v in category_counts.items()],
            'cateogry': signals_last_24h.count(),
        }

        return Response(data=data)
