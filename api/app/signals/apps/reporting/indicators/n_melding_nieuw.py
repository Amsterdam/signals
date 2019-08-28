from datetime import datetime

from django.db import connection

SQL = """
select
    parent_cat.slug as main_slug,
    cat.slug as sub_slug,
    count(*) as N_MELDING_NIEUW
from public.signals_signal as sig
    inner join public.signals_categoryassignment as cas
        on cas.id = sig.category_assignment_id
    inner join public.signals_category as cat
        on cas.category_id = cat.id
    inner join public.signals_category as parent_cat
        on cat.parent_id = parent_cat.id
where sig.created_at >= %(begin)s :: timestamp
    and sig.created_at < %(end)s :: timestamp
group by
    parent_cat.slug, cat.slug;
"""


class NMeldingNieuw:
    code = "N_MELDING_NIEUW"
    description = "Aantal open meldingen aan het eind van gegeven periode."

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
