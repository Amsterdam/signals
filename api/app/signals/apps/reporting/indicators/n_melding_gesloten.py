from datetime import datetime

from django.db import connection

SQL = """
select
    cat.id as category_id,
    cat.parent_id as parent_category_id,
    count(distinct(stat._signal_id)) as N_MELDING_GESLOT
from public.signals_status as stat
    inner join public.signals_signal as sig
        on sig.id = stat."_signal_id"
    inner join public.signals_categoryassignment as cas
        on sig.category_assignment_id = cas.id
    inner join public.signals_category as cat
        on cat.id = cas.category_id
where stat.created_at >= %(begin)s :: timestamp
    and stat.created_at < %(end)s :: timestamp
    and cat.parent_id is not null
group by cat.id;
"""


class NMeldingGesloten:
    code = "N_MELDING_GESLOT"
    description = "Aantal meldingen naar afgehandeld, geen dubbeltelling bij heropenen."

    sql = SQL

    def derive(self, begin, end, category, area):
        # Note: for know the following holds
        # - category granularity is per sub category
        # - area granularity is everywhere
        assert isinstance(begin, datetime)
        assert isinstance(end, datetime)

        with connection.cursor() as cursor:
            cursor.execute(self.sql, {'begin': begin, 'end': end})
            result = cursor.fetchall()
        return result
