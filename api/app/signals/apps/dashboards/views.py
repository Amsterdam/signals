import logging
from datetime import timedelta

from django.db import connection
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from signals.apps.signals import workflow
from signals.auth.backend import JWTAuthBackend

log = logging.getLogger(__name__)

SQL_COUNT_SIGNALS_PER_HOUR = \
    """
select
    ts, cast (extract(hour from ts) as integer) as h, count(signals_signal.id)
from
    generate_series(%s::timestamp, %s::timestamp - interval '1 hour', '1 hours') as ts
left join
    signals_signal
on
    signals_signal.created_at >= ts and signals_signal.created_at <= ts + interval '1 hour'
group by
    ts
order by
    ts;
"""

SQL_COUNTS_PER_MAIN_CATEGORY = \
    """
select
    signals_maincategory."name", count(signals_signal.id)
from
    signals_maincategory
left outer join
    signals_subcategory
on
    signals_subcategory.main_category_id = signals_maincategory.id
left outer join
    signals_categoryassignment
on
    signals_subcategory.id = signals_categoryassignment.sub_category_id
left outer join
    signals_signal
on
    signals_signal.id = signals_categoryassignment."_signal_id"
and
    signals_signal.created_at >= %s and signals_signal.created_at <= %s
group by
    signals_maincategory."name"
order by
    signals_maincategory."name"
;
"""

SQL_COUNT_PER_STATUS = \
    """
select
    signals_status.state, count(signals_signal.id)
from
    signals_status
left join
    signals_signal
on
    signals_signal.id = signals_status."_signal_id"
and
    signals_signal.created_at >= %s and signals_signal.created_at <= %s
group by
    signals_status.state
order by
    signals_status.state;
"""


class DashboardPrototype(APIView):
    authentication_classes = (JWTAuthBackend,)

    def _get_signals_per_status(self, report_start, report_end):
        """
        Count the number of Signals per status for given time interval.
        """
        with connection.cursor() as cursor:
            cursor.execute(SQL_COUNT_PER_STATUS, [report_start, report_end])
            signals_per_status_code = cursor.fetchall()

        mapping = {code: desc for code, desc in workflow.STATUS_CHOICES}
        signals_per_status = [
            {'name': mapping[code], 'count': count} for code, count in signals_per_status_code
        ]
        signals_per_status.sort(key=lambda x: x['name'].lower())

        return signals_per_status

    def _get_signals_per_category(self, report_start, report_end):
        """
        Count the number of Signals per main category for given time interval.
        """
        with connection.cursor() as cursor:
            cursor.execute(SQL_COUNTS_PER_MAIN_CATEGORY, [report_start, report_end])
            signals_per_main_category = cursor.fetchall()

        signals_per_category = [
            {'name': name, 'count': count} for name, count in signals_per_main_category
        ]

        return signals_per_category

    def _get_signals_per_hour(self, report_start, report_end):
        """
        Get Signal counts per hour for the given interval (assumption: rounded to hours).
        """

        with connection.cursor() as cursor:
            cursor.execute(SQL_COUNT_SIGNALS_PER_HOUR, [report_start, report_end])
            signals_per_hour = cursor.fetchall()

        return [{
            "interval_start": ts,
            "hour": hr,
            "count": cnt
        } for ts, hr, cnt in signals_per_hour]

    def get(self, request, format=None):
        """
        Prepare dashboard data.
        """
        now = timezone.now()
        # Round up to next full hour, use that as end of report. If we are exactly at
        # the start of an hour, still move the end time to next hour.
        report_end = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        # Start of reporting is 24 hours earlier:
        report_start = report_end - timedelta(days=1)

        data = {
            'hour': self._get_signals_per_hour(report_start, report_end),
            'category': self._get_signals_per_category(report_start, report_end),
            'status': self._get_signals_per_status(report_start, report_end),
        }

        return Response(data=data)
