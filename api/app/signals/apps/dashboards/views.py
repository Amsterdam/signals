from collections import defaultdict
from datetime import timedelta
import logging

from django.db import connection
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from signals.apps.signals import workflow
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend

log = logging.getLogger(__name__)


# See: https://www.postgresql.org/docs/10/functions-datetime.html for date_trunc
SQL_COUNT_SIGNALS_PER_HOUR = \
"""
SELECT
    date_trunc('hour', "created_at") as "h", count(*)
FROM
    "signals_signal"
WHERE
    "created_at" >= %s and "created_at" <= %s
GROUP BY
    "h"
ORDER BY
    "h";
"""

SQL_COUNTS_PER_MAIN_CATEGORY = \
"""
select
	signals_maincategory."name", count(signals_maincategory."name")
from
	signals_signal
left outer join
	signals_categoryassignment
on
	signals_signal.id = signals_categoryassignment._signal_id
left outer join
	signals_subcategory
on
	signals_categoryassignment.sub_category_id = signals_subcategory.id
left outer join
	signals_maincategory
on
	signals_subcategory.main_category_id = signals_maincategory.id
where
	signals_signal.created_at >= %s and signals_signal.created_at <= timestamp %s
group by
	signals_maincategory."name"
order by
	signals_maincategory."name";
"""

SQL_COUNT_PER_STATUS = \
"""
select
	signals_status.state, count(signals_status.state)
from
	signals_signal
left outer join
	signals_status
on
	signals_signal.id = signals_status._signal_id
where
	signals_signal.created_at >= %s and signals_signal.created_at <= %s
group by
	signals_status.state
order by
	signals_status.state;
"""


class DashboardProtype(APIView):
    authentication_classes = (JWTAuthBackend, )

    def _get_signals_per_status(self, report_start, report_end):
        """
        Count the number of Signals per status for given time interval.
        """
        with connection.cursor() as cursor:
            cursor.execute(SQL_COUNT_PER_STATUS, [report_start, report_end])
            signals_per_status_code = cursor.fetchall()

        mapping = {code: desc for code, desc in workflow.STATUS_CHOICES}
        signals_per_status = [
            {'name': mapping[code], 'count':  count} for code, count in signals_per_status_code
        ]

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

        return signals_per_main_category

    def _get_signals_per_hour(self, report_start, report_end):
        """
        Get Signal counts per hour for the given interval (assumption: rounded to hours).
        """
        with connection.cursor() as cursor:
            cursor.execute(SQL_COUNT_SIGNALS_PER_HOUR, [report_start, report_end])
            signals_per_hour = cursor.fetchall()

        # Assuming report_start and report_end are rounded to hours we fill in
        # any missing entries. We want an entry for each hour in the interval;
        # if there are no signals in some hourly interval we add an enty with 0.
        out = []
        signals_per_hour.sort(key=lambda x: x[0])
        signals_per_hour.reverse()

        # create placeholders in case we need to fix missing entries
        t_interval_start = report_start
        if signals_per_hour:
            earliest_entry = signals_per_hour.pop()
        else:
            # Choose entry outside of interval, will not be used.
            earliest_entry = ((report_end + timedelta(hours=1), 0))

        while t_interval_start < report_end:
            if t_interval_start == earliest_entry[0]:
                out.append(earliest_entry)

                earliest_entry = signals_per_hour.pop() if signals_per_hour else ((report_end + timedelta(hours=1), 0))

            elif t_interval_start < earliest_entry[0]:
                out.append((t_interval_start, 0))
            else:
                # this should not happen
                raise Exception()
            t_interval_start += timedelta(hours=1)

        return out

    def get(self, request, format=None):
        """
        Prepare dashboard data.
        """
        now = timezone.now()
        # Round up to next full hour, use that as end of report. If we are exactly at
        # the start of an hour, still move the end time to next hour.
        report_end = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        # Start of reporting is 24 hours earlier:
        report_start = report_end - timedelta(days=1

        data = {
            'hour': self._get_signals_per_hour(report_start, report_end),
            'category': self._get_signals_per_category(report_start, report_end),
            'status': self._get_signals_per_status(report_start, report_end),
        }

        return Response(data=data)
